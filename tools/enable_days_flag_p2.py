"""Bước CLI Phase 2: khai báo --days an toàn, chưa bật DayController.

Chạy từ root repository: python3 tools/enable_days_flag_p2.py
Không viết lại runner/gameplay hay đổi manifest chính thức.
"""
from pathlib import Path
import ast
import sys

TARGET = Path('chonoi/headless.py')
ANCHOR = '    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)\n'
OLD_GUARD = ('        if a.mode == "day":\n'
             '            raise BadInput("--mode day chưa hỗ trợ ở contract v1.0 (có từ v1.1)")\n')
NEW_GUARD = ('        if a.days is not None and a.mode != "day":\n'
             '            raise BadInput("--days chỉ dùng với day")\n'
             '        if a.mode == "day" and a.days is not None and not 1 <= a.days <= 5:\n'
             '            raise BadInput("--days phải thuộc [1, 5]")\n'
             '        if a.mode == "day":\n'
             '            # TODO(P2): thay guard bằng lời gọi DayController sau khi hợp đồng v1.1 được kích hoạt.\n'
             '            raise BadInput("--mode day chưa hỗ trợ ở contract v1.0 (có từ v1.1)")\n')

def main():
    if not TARGET.is_file():
        sys.exit('Không tìm thấy chonoi/headless.py; hãy chạy từ root repository.')
    old = TARGET.read_text(encoding='utf-8')
    if 'p.add_argument("--days"' in old:
        sys.exit('Phát hiện --days đã tồn tại, không ghi đè. Hãy kiểm tra thủ công.')
    if old.count(ANCHOR) != 1 or old.count(OLD_GUARD) != 1:
        sys.exit('Cấu trúc headless.py đã thay đổi: từ chối vá tự động để tránh mất code.')
    new = old.replace(ANCHOR, ANCHOR +
        '    p.add_argument("--days", type=_int("days"), default=None,\n'
        '                   help="số Ngày từ 1 đến 5, chỉ dùng với --mode day (mặc định 1)")\n', 1)
    new = new.replace(OLD_GUARD, NEW_GUARD, 1)
    ast.parse(new, filename=str(TARGET))
    TARGET.write_text(new, encoding='utf-8')
    print('Patched chonoi/headless.py: --days hợp lệ trong day, giữ guard runtime v1.0.')
    print('Quan trọng: Day Controller chưa được triển khai; --mode day vẫn trả mã 2.')

if __name__ == '__main__':
    main()
