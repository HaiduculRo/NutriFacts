import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neural_network import MLPClassifier

#eliminam ce nu ne intereseaza
df = pd.read_csv('nutrition_with_grades.csv', dtype={'code': str})
df = df.drop(columns=['code'])
df = df.dropna()

#Separare caracteristici de etichete
X = df.drop(columns=['nutri_score'])  
y = df['nutri_score']                 

# Convertim etichetele (A-E) în valori numerice
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# 90 train si 10 val
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.1, random_state=42)

# # Random Forest
# model = RandomForestClassifier(random_state=42)
# model.fit(X_train, y_train)

# print("REZULTATE RANDOM FOREST")
# # Afișăm rezultate
# y_pred = model.predict(X_test)
# print("Acuratețea pe setul de test: {:.2f}%".format(accuracy_score(y_test, y_pred) * 100))
# print("\nRaport detaliat:\n")
# print(classification_report(y_test, y_pred, target_naWmes=label_encoder.classes_))

model = xgb.XGBClassifier(n_estimators=500, random_state=100)
model.fit(X_train, y_train)

# print("_______________________\nREZULTATE XGBOOST")
# # Afișăm rezultate
# y_pred = model.predict(X_test)
# print("Acuratețea pe setul de test: {:.2f}%".format(accuracy_score(y_test, y_pred) * 100))
# print("\nRaport detaliat:\n")
# print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# cm = confusion_matrix(y_test, y_pred)
# class_names = label_encoder.classes_

# plt.figure(figsize=(8, 6))
# sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
#             xticklabels=class_names,
#             yticklabels=class_names)

# plt.xlabel('Etichete Prezise')
# plt.ylabel('Etichete Adevărate')
# plt.title('Matrice de Confuzie - XGBoost')
# plt.show()


# param_grid = {
#     'n_neighbors': list(range(1, 4)),
#     'weights': ['uniform', 'distance'],
#     'metric': ['euclidean', 'manhattan']
# }

# grid = GridSearchCV(KNeighborsClassifier(), param_grid, cv=5, scoring='accuracy', n_jobs=-1)
# grid.fit(X_train, y_train)

# print("🔍 Cel mai bun model KNN:")
# print(grid.best_estimator_)
# print(f"Acuratețea validată: {grid.best_score_:.2f}")






# Exemplu de predicție
# exemplu = X_test.iloc[0]
# predictie = model.predict([exemplu])[0]
# eticheta = label_encoder.inverse_transform([predictie])[0]

# print(f"\n🔍 Exemplu de produs:\n{exemplu}")
# print(f"👉 Modelul prezice Nutri-Score: {eticheta}")

#rezultate

#   1) KNeighborsClassifier + Parametrii
#       KNeighborsClassifier(metric='manhattan', n_neighbors=3, weights='distance')       
#       Acuratețea validată: 0.87

#   2) Random Forest
#       Acuratețea pe setul de test: 96.16%

#   3) Xgboost
#       Acuratețea pe setul de test: 96.75%

#   4) Xgboost + HiperParametrii
#       Acuratețea pe setul de test: 97.20%

# model = RandomForestClassifier(
#     n_estimators=500,              # 200 arbori
#     n_jobs=-1,                     # Folosește toate nucleele procesorului
#     random_state=100,               # Pentru reproducibilitatea rezultatelor      
#     bootstrap=True,                # Tratează clasele dezechilibrate
# )

# model.fit(X_train, y_train)

# print("REZULTATE RANDOM FOREST")
# # Afișăm rezultate
y_pred = model.predict(X_test)
print("Acuratețea pe setul de test: {:.2f}%".format(accuracy_score(y_test, y_pred) * 100))
print("\nRaport detaliat:\n")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
