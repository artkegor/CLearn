import os
import shlex
import asyncio
from logging_config import setup_logging

logger = setup_logging()


async def run_c_task_in_sandbox(filename: str, test_cases: list[dict]) -> dict:
    """
    Run C code in a sandboxed Docker environment and test against provided test cases.
    :param filename: File path to the C source code.
    :param test_cases: Test cases with 'input' and 'expected_output' keys.
    :return: Log of results and counts of passed/total tests.
    """
    abs_path = os.path.abspath(filename)
    workdir = os.path.dirname(abs_path)
    log_lines = []
    passed = 0
    total = len(test_cases)

    # Compilation step
    compile_cmd = f"docker run --rm --network none --pids-limit 64 --memory 256m --memory-swap 256m " \
                  f"--cpus 0.5 --read-only --tmpfs /tmp:exec,mode=1777 --security-opt no-new-privileges:true " \
                  f"--cap-drop ALL -v {workdir}:/sandbox:rw -w /sandbox c-sandbox " \
                  f"gcc {shlex.quote(os.path.basename(filename))} -o user -lm 2> app.log"

    compile_proc = await asyncio.create_subprocess_shell(
        compile_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    logger.info(f"Compiling {filename} in sandbox...")
    await compile_proc.wait()

    if compile_proc.returncode != 0:
        logger.error(f"Compilation failed for {filename} in sandbox with return code {compile_proc.returncode}.")
        err_path = os.path.join(workdir, "app.log")
        err = ""
        if os.path.exists(err_path):
            with open(err_path) as f:
                err = f.read()
        log_lines.append(f"❌ Ошибка компиляции:\n{err}")
        return {"log": "\n".join(log_lines), "passed": 0, "total": total}
    else:
        logger.info(f"Successfully compiled {filename} in sandbox.")

    # Test cases execution
    for i, t in enumerate(test_cases, start=1):
        input_data = str(t["input"]).strip()
        expected = str(t["expected_output"]).strip()

        run_cmd = f'docker run --rm --network none --pids-limit 64 --memory 128m --memory-swap 128m ' \
                  f'--cpus 0.5 --read-only --tmpfs /tmp:exec,mode=1777 --security-opt no-new-privileges:true ' \
                  f'--cap-drop ALL -v {workdir}:/sandbox:rw -w /sandbox c-sandbox ' \
                  f'/bin/bash -c "echo {shlex.quote(input_data)} | ./user"'

        proc = await asyncio.create_subprocess_shell(
            run_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(input_data.encode()), timeout=4)
        except asyncio.TimeoutError:
            await proc.kill()
            log_lines.append(f"Тест {i}: {t.get('description', '')}\n    ❌ Превышено время выполнения\n")
            continue

        stdout_str = stdout.decode().strip()
        correct = stdout_str == expected
        symbol = "✅" if correct else "❌"
        if correct:
            passed += 1

        log_lines.append(f"Тест {i}")
        log_lines.append(f"{symbol} Ввод: {input_data}")
        log_lines.append(f"Ожидалось: {expected}\n"
                         f"Получено: {stdout_str}")
        if stderr:
            log_lines.append(f"    (stderr): {stderr.decode().strip()}")
        log_lines.append("")

    log_lines.append(f"📊 Результат: {passed}/{total} тестов пройдено.")

    return {"log": "\n".join(log_lines), "passed": passed, "total": total}
