import sys
sys.path.insert(0, 'review')
from agent import get_git_diff, review_diff, generate_report, save_report

diff = get_git_diff()
print('Diff长度:', len(diff))

if diff:
    result = review_diff(diff)
    report = generate_report(result)
    print(report)
    save_report(report)
else:
    print('无变更')