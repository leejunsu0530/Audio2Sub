import os
import sys
from typing import Literal, Callable, Any
import importlib.metadata
from packaging import version
import requests
import subprocess
import shlex
from rich.text import Text
from rich.panel import Panel
from rich.live import Live
from rich.prompt import Prompt

from .console import console


def execute_cmd_realtime(command: str, print_: Callable = print, print_kwargs: dict = None, wait: bool = True):
    """run보다 복잡하고 많은 기능을 제공하는 popen 기능 사용
    Args:
        command: 실행할 명령어 문자열
        print_: 출력 함수. 필요시 rich의 console.print로 변경
        print_kwargs: print_에 전달할 인자 목록. rich를 쓸때의 {highlight: True} 등. 없는거 전달달하면 에러나니 주의
        wait: false로 하면 명령어가 끝나는 걸 기다리지 않고 다음 파이썬 구문으로 넘어감
    """
    process = None
    # cmd = shlex.split(command) # 이건 대괄호 들어간 문자열 깨짐
    if print_kwargs is None:
        print_kwargs = {}

    program, left_command = command.split(" ", 1)
    print(f"Command: \033[33m{program}\033[0m {left_command}")

    try:
        process = subprocess.Popen(
            # cmd,
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # 버퍼링 방식 지정. 1줄씩 출력에 필요
        )

        if process.stdout is None:
            raise RuntimeError("stdout을 가져오지 못했습니다.")

        # Popen이 성공했을 때만 stdout 읽기
        for line in iter(process.stdout.readline, ''):
            print_(line.rstrip(), **print_kwargs)

    except Exception:
        # Popen은 성공했는데 실행 중 에러 발생 시 생성된 서브프로세스 종료
        if process:
            process.terminate()
        raise  # 예외 다시 발생

    finally:
        if process and wait:
            process.wait()


def ask_choice(msg: str, choice: list[Any] | tuple[Any] | None = None, default: Any = None) -> str:
    """default를 안전하게 처리함"""
    str_choice: list[str] | None = [str(c) for c in choice] if choice else None
    default_dict: dict[Literal["default"], str] = {}
    if default is not None:  # 그냥 not 쓰면 0같은거 무시됨
        default_dict["default"] = str(default)

    # type: ignore
    return Prompt.ask(msg, choices=str_choice, **default_dict, console=console)


def ask_y_or_n(msg: str, default: str = "n") -> bool:
    if ask_choice(msg, ["y", "n"], default) == "y":
        return True
    else:
        return False


def get_current_version(package_name: str) -> tuple[str | None, str]:
    """
    Return:
        (version, message)
    """
    try:
        v = importlib.metadata.version(package_name)
        return v, f"설치된 현재 버전: {v}"
    except importlib.metadata.PackageNotFoundError:
        return None, "패키지를 찾을 수 없습니다."


def get_latest_version_pypi(package_name: str) -> tuple[str | None, str]:
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        latest_version = data["info"]["version"]
        return latest_version, f"최신 {package_name} 버전: {latest_version}"
    else:
        return None, "PyPI에서 데이터를 가져오는 중 오류 발생"


def compare_version(current_version: str, latest_version: str) -> tuple[bool, str]:
    if version.parse(current_version) < version.parse(latest_version):
        return True, "업데이트가 필요합니다."
    else:
        return False, "이미 최신 버전을 사용 중입니다."


def update_module(to_update: str, print_: Callable = print, print_kwargs: dict = None) -> None:
    execute_cmd_realtime(
        f"{sys.executable} -m pip install --upgrade {to_update}", print_, print_kwargs)


def check_and_update_in_panel(module_name: str, module_name_to_update: str,
                              update: bool | Literal["ask"] = "ask") -> Literal[1] | Literal[0]:
    new_console = console
    lines = []

    def updater(new_line: str) -> None:
        lines.append(new_line)
        panel_text = new_console.highlighter(
            Text("\n".join(lines), style="bold"))
        live.update(Panel(panel_text))  # 클로져 지원되니까 이거 문제 x

    with Live(Panel("시작 중..."), console=new_console, refresh_per_second=4, transient=False) as live:
        if not module_name_to_update:
            module_name_to_update = module_name

        updater(f"현재 가상환경: {sys.executable}")
        updater(f"모듈 이름: {module_name}")

        current_version, message = get_current_version(module_name)
        updater(message)
        if not current_version:
            return 1  # 오류로 종료

        latest_version, message = get_latest_version_pypi(module_name)
        updater(message)
        if not latest_version:
            return 1

        need_update, message = compare_version(current_version, latest_version)
        updater(message)  # 이 아래 질문에서 꺠지기 때문에 별도의 패널로 분리

    lines = []
    if need_update:
        if update == "ask":
            update = ask_y_or_n("모듈을 업데이트하시겠습니까?")

        if update:  # true면
            with Live(Panel("시작 중..."), console=new_console, refresh_per_second=4, transient=False) as live:
                update_module(module_name_to_update, updater)
        print()
    return 0
