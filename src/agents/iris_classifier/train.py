"""Offline training script for Iris Classifier model."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.iris_classifier.agent import IrisClassifierAgent


def main():
    """Train the Iris Classifier model offline."""
    print("=" * 60)
    print("🌺 Iris Classifier - Model Training")
    print("=" * 60)
    print()
    
    # Initialize agent with default model path
    model_path = Path(__file__).parent / "models" / "iris_rf_model.pkl"
    
    agent = IrisClassifierAgent(
        model_path=str(model_path),
        n_estimators=100,
        random_state=42,
    )
    
    # Train model
    print("Starting training...")
    print()
    metrics = agent.train_model()
    
    # Display results
    print()
    print("=" * 60)
    print("✅ Training Complete!")
    print("=" * 60)
    print(f"📊 Training Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"📊 Test Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"🌳 Number of Trees: {metrics['n_estimators']}")
    print(f"💾 Model saved to: {metrics['model_path']}")
    print()
    print("📈 Feature Importances:")
    for feature, importance in metrics['feature_importances'].items():
        print(f"  - {feature}: {importance:.4f}")
    print()
    print("=" * 60)
    print("The model is now ready for inference!")
    print("=" * 60)


if __name__ == '__main__':
    main()

