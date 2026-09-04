import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import re

# 한글 폰트 설정 (없으면 자동으로 나눔고딕 다운로드 시도, 실패해도 그래프는 그려짐)
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'NanumGothic'

# ------------------------------
# 1. 데이터 불러오기 + 정제
# ------------------------------
df = pd.read_csv('/home/claude/stardew/stardew_raw.csv')

# "2026년 8월" -> datetime으로 변환
def parse_month(s):
    m = re.match(r'(\d+)년 (\d+)월', s)
    year, month = int(m.group(1)), int(m.group(2))
    return pd.Timestamp(year=year, month=month, day=1)

df['날짜'] = df['월'].apply(parse_month)
df = df.sort_values('날짜').reset_index(drop=True)

# 증감률 컬럼: "%" 제거하고 숫자로
df['증감률_num'] = df['증감률'].astype(str).str.replace('%', '').replace('nan', None)
df['증감률_num'] = pd.to_numeric(df['증감률_num'], errors='coerce')

print("=== 기본 정보 ===")
print(f"데이터 기간: {df['날짜'].min().strftime('%Y-%m')} ~ {df['날짜'].max().strftime('%Y-%m')}")
print(f"총 데이터 포인트 수: {len(df)}개")
print(f"결측치 개수:\n{df.isna().sum()}")

# ------------------------------
# 2. 이상치 처리
# ------------------------------
# 게임 출시일: 2016-02-26. 그 이전 달(2015년 12월, 2016년 1월)은
# 출시 전이라 평균 접속자가 0~1명 수준 -> 정상적인 게임 데이터가 아니라 "출시 전 노이즈"이므로 제외
before_launch = df[df['날짜'] < '2016-02-01']
print(f"\n출시 전 데이터로 판단해 제외: {before_launch['월'].tolist()}")
df = df[df['날짜'] >= '2016-02-01'].reset_index(drop=True)

print(f"정제 후 데이터 포인트 수: {len(df)}개")

# ------------------------------
# 3. 시계열 분석 기법 적용
# ------------------------------
# 기법 1: 3개월 이동평균 (단기 노이즈를 부드럽게 보기 위해)
df['이동평균_3개월'] = df['평균플레이어'].rolling(window=3).mean()

# 기법 2: 연도별 통계 (연도별 평균/최고 접속자)
df['연도'] = df['날짜'].dt.year
yearly = df.groupby('연도').agg(
    연평균접속자=('평균플레이어', 'mean'),
    연최고접속자=('피크플레이어', 'max')
).reset_index()

df.to_csv('/home/claude/stardew/stardew_clean.csv', index=False, encoding='utf-8-sig')
yearly.to_csv('/home/claude/stardew/stardew_yearly.csv', index=False, encoding='utf-8-sig')

print("\n=== 연도별 통계 ===")
print(yearly.to_string(index=False))

# ------------------------------
# 4. 시각화
# ------------------------------

# 그래프 1: 전체 기간 월별 평균 접속자 + 3개월 이동평균
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['날짜'], df['평균플레이어'], color='#94a3b8', linewidth=1, label='월별 평균 접속자 (원본)')
ax.plot(df['날짜'], df['이동평균_3개월'], color='#dc2626', linewidth=2, label='3개월 이동평균')

# 주요 업데이트 시점 표시
updates = {
    '2018-11': '1.3',
    '2019-12': '1.4',
    '2021-01': '1.5',
    '2024-03': '1.6',
}
for date_str, label in updates.items():
    d = pd.Timestamp(date_str)
    ax.axvline(d, color='#059669', linestyle='--', alpha=0.5)
    ax.text(d, ax.get_ylim()[1]*0.95, f'{label} 업데이트', rotation=90,
            fontsize=8, color='#059669', va='top')

ax.set_title('스타듀밸리 Steam 월별 평균 동시 접속자 수 (2016~2026)', fontsize=14)
ax.set_xlabel('날짜')
ax.set_ylabel('평균 동시 접속자 수 (명)')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('/home/claude/stardew/01_전체추이_이동평균.png', dpi=150)
plt.close()

# 그래프 2: 연도별 평균/최고 접속자 막대그래프
fig, ax = plt.subplots(figsize=(10, 6))
x = yearly['연도'].astype(str)
width = 0.35
ax.bar([i - width/2 for i in range(len(x))], yearly['연평균접속자'], width, label='연평균 접속자', color='#3b82f6')
ax.bar([i + width/2 for i in range(len(x))], yearly['연최고접속자'], width, label='연중 최고 접속자', color='#f59e0b')
ax.set_xticks(range(len(x)))
ax.set_xticklabels(x, rotation=45)
ax.set_title('연도별 평균 접속자 수 vs 연중 최고 접속자 수', fontsize=14)
ax.set_ylabel('접속자 수 (명)')
ax.legend()
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('/home/claude/stardew/02_연도별_비교.png', dpi=150)
plt.close()

# 그래프 3: 전월 대비 변화율 (급등/급락 확인용)
# 주의: 2016년 2~3월은 "출시 직후 0명 -> 정상 수준" 구간이라 증감률이 수만~수십만%로 튀는
# 이상치임. 실제 게임 운영 기간의 변화 패턴을 보려면 이 구간을 제외하는 게 합리적.
df_pct = df[df['날짜'] >= '2016-04-01']
fig, ax = plt.subplots(figsize=(12, 6))
colors = ['#dc2626' if v < 0 else '#059669' for v in df_pct['증감률_num'].fillna(0)]
ax.bar(df_pct['날짜'], df_pct['증감률_num'], color=colors, width=20)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_title('전월 대비 평균 접속자 증감률 (%)', fontsize=14)
ax.set_xlabel('날짜')
ax.set_ylabel('증감률 (%)')
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('/home/claude/stardew/03_전월대비_증감률.png', dpi=150)
plt.close()

print("\n그래프 3개 저장 완료:")
print("- 01_전체추이_이동평균.png")
print("- 02_연도별_비교.png")
print("- 03_전월대비_증감률.png")

# ------------------------------
# 5. 참고용 관찰 포인트 출력 (인사이트 작성에 참고하라고 출력만 함)
# ------------------------------
print("\n=== 참고: 극단값 top 5 (증감률 기준, 출시 초반 제외) ===")
stable = df[df['날짜'] >= '2017-01-01']
print(stable.nlargest(5, '증감률_num')[['월', '평균플레이어', '증감률_num']].to_string(index=False))
print("\n=== 참고: 하락 top 5 ===")
print(stable.nsmallest(5, '증감률_num')[['월', '평균플레이어', '증감률_num']].to_string(index=False))
