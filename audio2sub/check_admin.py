import ctypes

# 0. 관리자 권한 체크
try:
    # 성공하면 1, 실패하면 0을 반환합니다.
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
except (AttributeError, OSError):
    is_admin = 1  # pylint: disable=invalid-name
if not is_admin:
    print_and_exit(
        "[red] [오류] 관리자 권한으로 실행되어 있지 않습니다. 이 스크립트는 관리자 권한이 필요합니다.[/red]", success=False)
