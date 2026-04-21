"""
One-shot training for the Alzheimer's prediction pipeline.
Trains the 4 RF regressors + logistic classifier and saves them to
models/pipeline.joblib. Run once; then final_v.py will load from the
saved file instead of retraining each time.
"""

from final_v import train_rf_models, train_classifier, save_pipeline


def main():
    print("Training Random Forest models...")
    models, medians = train_rf_models()

    print("\nTraining diagnosis classifier...")
    clf, _ = train_classifier()

    print("\nSaving pipeline...")
    save_pipeline(models, medians, clf)
    print("Done.")


if __name__ == "__main__":
    main()
