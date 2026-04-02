import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def check_file():
    # Make sure we use the right name
    csv_path = "Job Datsset.csv"
    if not os.path.exists(csv_path):
        csv_path = "Job Dataset.csv" # fallback
    return csv_path

def main():
    print("Loading dataset...")
    csv_path = check_file()
    df = pd.read_csv(csv_path)

    # Basic preprocessing
    print("Preprocessing data...")
    # Fill NaN with empty strings if any
    df['User_Skills'] = df['User_Skills'].fillna('')
    df['Job_Requirements'] = df['Job_Requirements'].fillna('')

    # We will combine User_Skills and Job_Requirements into a single text feature 
    # for each row to learn the relationship, or we can vectorize them separately 
    # and combine the vectors. Separately is usually better to differentiate user vs job.
    
    # Initialize Vectorizers
    user_vectorizer = TfidfVectorizer(max_features=500)
    job_vectorizer = TfidfVectorizer(max_features=500)

    print("Vectorizing text...")
    X_user = user_vectorizer.fit_transform(df['User_Skills']).toarray()
    X_job = job_vectorizer.fit_transform(df['Job_Requirements']).toarray()

    # Combine features (horizontal stack)
    import numpy as np
    X = np.hstack((X_user, X_job))
    y = df['Recommended'].values

    # Train-test split
    print("Splitting data into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and train model
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # Evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save models
    print("Saving model and vectorizers...")
    joblib.dump(model, 'job_recommendation_model.pkl')
    joblib.dump(user_vectorizer, 'user_vectorizer.pkl')
    joblib.dump(job_vectorizer, 'job_vectorizer.pkl')
    
    print("Training complete! Artifacts saved.")

if __name__ == "__main__":
    main()
