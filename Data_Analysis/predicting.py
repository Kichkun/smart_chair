import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

pd.options.display.max_columns = 15
plt.interactive(True)

df = pd.read_csv('../data/clean/df_merged.csv')

skill_dict = {
    'Small': 0,
    'Huge': 1,
}


df['Skill'] = df['Skill'].apply(lambda x: skill_dict[x])

target = df['Skill']
train = df.drop(['Skill', 'player_name'], axis=1, errors='ignore')
# train = df.drop(['player_name'], axis=1, errors='ignore')

# Heatmap
plt.imshow(train.corr())

# LR training
lr = LogisticRegression(class_weight='balanced')
train_part = train.iloc[:, :]
lr.fit(train_part, target.values.reshape(-1))
lr.predict(train_part)
predict = lr.predict_proba(train_part)[:, 1]


roc_auc_score(target, predict)












