import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv('stardew_raw.csv')
print(df)
import re

def parse_month(s):
    m = re.match(r'(\d+)년 (\d+)월', s)
    year = int(m.group(1))
    month = int(m.group(2))
    return pd.Timestamp(year=year, month=month, day=1)

df['날짜'] = df['월'].apply(parse_month)
print(df['날짜'])
df = df.sort_values('날짜').reset_index(drop=True)
print(df.head())
df = df[df['날짜'] >= '2016-02-01'].reset_index(drop=True)
print(f'정제 후 데이터 개수: {len(df)}개')
df['이동평균_3개월'] = df['평균플레이어'].rolling(window=3).mean()
print(df[['월', '평균플레이어', '이동평균_3개월']].head(6))
df['연도'] = df['날짜'].dt.year
yearly = df.groupby('연도')['평균플레이어'].mean()
print(yearly)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(12, 6))
plt.plot(df['날짜'], df['평균플레이어'], color='gray', label='원본')
plt.plot(df['날짜'], df['이동평균_3개월'], color='red', linewidth=2, label='3개월 이동평균')
plt.title('스타듀밸리 월별 평균 접속자 수')
plt.xlabel('날짜')
plt.ylabel('평균 접속자 수')
plt.legend()
plt.savefig('my_graph1.png')
print('그래프 저장 완료!')
plt.figure(figsize=(10, 6))
plt.bar(yearly.index.astype(str), yearly.values, color='skyblue')
plt.title('연도별 평균 접속자 수')
plt.xlabel('연도')
plt.ylabel('평균 접속자 수')
plt.xticks(rotation=45)
plt.savefig('my_graph2.png')
print('그래프2 저장 완료!')
