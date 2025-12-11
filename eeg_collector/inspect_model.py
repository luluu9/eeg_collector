import joblib
import sys
import os

model_path = os.path.join(os.path.dirname(__file__), 'models', 'csp_svm_mati_model.pkl')

try:
    with open(model_path, 'rb') as f:
        model = joblib.load(f)
    
    print(f"Model type: {type(model)}")
    
    if hasattr(model, 'classes_'):
        print(f"Classes: {model.classes_}")
    
    if hasattr(model, 'steps'):
        print("Pipeline steps:")
        for name, step in model.steps:
            print(f"  - {name}: {type(step)}")
            if hasattr(step, 'n_components'):
                print(f"    n_components: {step.n_components}")
                
    # Check if it has an internal classifier
    if hasattr(model, 'estimator'):
        print(f"Estimator: {type(model.estimator)}")

except Exception as e:
    print(f"Error loading model: {e}")
