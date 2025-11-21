"""Iris Classifier Agent using Random Forest from scikit-learn."""
import json
import pickle
from pathlib import Path
from typing import Any, AsyncGenerator

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split


class IrisClassifierAgent:
    """ML Pipeline Agent for Iris flower classification using Random Forest."""
    
    def __init__(
        self,
        model_path: str = "./models/iris_rf_model.pkl",
        n_estimators: int = 100,
        random_state: int = 42,
    ):
        """Initialize the Iris Classifier Agent.
        
        Args:
            model_path: Path to save/load the trained model
            n_estimators: Number of trees in the Random Forest
            random_state: Random seed for reproducibility
        """
        print(f"[DEBUG] Initializing IrisClassifierAgent")
        print(f"[DEBUG] Model path: {model_path}")
        print(f"[DEBUG] N estimators: {n_estimators}")
        
        self.model_path = Path(model_path)
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: RandomForestClassifier | None = None
        self.feature_names = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
        self.class_names = ['setosa', 'versicolor', 'virginica']
        
        # Ensure model directory exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load model if it exists, otherwise it needs to be trained
        self._load_model()
        
        print("[DEBUG] IrisClassifierAgent initialized")
    
    def _load_model(self) -> None:
        """Load the trained model from disk."""
        if self.model_path.exists():
            print(f"[DEBUG] Loading trained model from {self.model_path}")
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("[DEBUG] Model loaded successfully")
            except Exception as e:
                print(f"[DEBUG] ERROR: Failed to load model: {e}")
                self.model = None
        else:
            print("[DEBUG] No trained model found. Model needs to be trained.")
            self.model = None
    
    def train_model(self) -> dict[str, Any]:
        """Train the Random Forest classifier on Iris dataset.
        
        This method should be called offline to train the model.
        
        Returns:
            Dictionary with training metrics
        """
        print("[DEBUG] Starting model training...")
        
        # Load Iris dataset
        iris = load_iris()
        X, y = iris.data, iris.target
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )
        
        # Train Random Forest
        print("[DEBUG] Training Random Forest classifier...")
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"[DEBUG] Training accuracy: {train_score:.4f}")
        print(f"[DEBUG] Test accuracy: {test_score:.4f}")
        
        # Save model
        print(f"[DEBUG] Saving model to {self.model_path}")
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Calculate feature importances
        feature_importances = dict(zip(self.feature_names, self.model.feature_importances_))
        
        metrics = {
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'n_estimators': self.n_estimators,
            'feature_importances': feature_importances,
            'model_path': str(self.model_path),
        }
        
        print("[DEBUG] Model training complete")
        return metrics
    
    def predict(self, features: list[float] | dict[str, float]) -> dict[str, Any]:
        """Make a prediction on input features.
        
        Args:
            features: Either a list of 4 feature values [sepal_length, sepal_width, 
                     petal_length, petal_width] or a dict with feature names as keys
        
        Returns:
            Dictionary with prediction results including:
            - predicted_class: Name of predicted class
            - class_id: Numeric class ID
            - probabilities: Dict of class probabilities
            - confidence: Confidence score (max probability)
        """
        if self.model is None:
            return {
                'error': 'Model not trained. Please train the model first using train_model().',
                'predicted_class': None,
                'class_id': None,
                'probabilities': {},
                'confidence': 0.0,
            }
        
        # Convert input to numpy array
        if isinstance(features, dict):
            # Extract features in correct order
            feature_array = np.array([
                features.get('sepal_length', 0.0),
                features.get('sepal_width', 0.0),
                features.get('petal_length', 0.0),
                features.get('petal_width', 0.0),
            ])
        else:
            # Assume list of 4 values
            if len(features) != 4:
                return {
                    'error': f'Expected 4 features, got {len(features)}',
                    'predicted_class': None,
                    'class_id': None,
                    'probabilities': {},
                    'confidence': 0.0,
                }
            feature_array = np.array(features)
        
        # Reshape for single prediction
        feature_array = feature_array.reshape(1, -1)
        
        # Make prediction
        prediction = self.model.predict(feature_array)[0]
        probabilities = self.model.predict_proba(feature_array)[0]
        
        # Format results
        result = {
            'predicted_class': self.class_names[prediction],
            'class_id': int(prediction),
            'probabilities': {
                self.class_names[i]: float(prob)
                for i, prob in enumerate(probabilities)
            },
            'confidence': float(max(probabilities)),
        }
        
        return result
    
    def parse_input(self, input_text: str) -> dict[str, float] | None:
        """Parse input text to extract feature values.
        
        Supports multiple formats:
        - JSON: {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        - List: [5.1, 3.5, 1.4, 0.2]
        - Space-separated: "5.1 3.5 1.4 0.2"
        - Comma-separated: "5.1, 3.5, 1.4, 0.2"
        
        Args:
            input_text: Input text containing feature values
        
        Returns:
            Dictionary with feature names and values, or None if parsing fails
        """
        input_text = input_text.strip()
        
        # Try JSON first
        try:
            data = json.loads(input_text)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                if len(data) == 4:
                    return {
                        'sepal_length': float(data[0]),
                        'sepal_width': float(data[1]),
                        'petal_length': float(data[2]),
                        'petal_width': float(data[3]),
                    }
        except json.JSONDecodeError:
            pass
        
        # Try space-separated or comma-separated
        try:
            # Replace commas with spaces and split
            values = input_text.replace(',', ' ').split()
            if len(values) == 4:
                return {
                    'sepal_length': float(values[0]),
                    'sepal_width': float(values[1]),
                    'petal_length': float(values[2]),
                    'petal_width': float(values[3]),
                }
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the prediction response back to the client.
        
        Args:
            query: User query containing feature values
        
        Yields:
            Dict with 'content' and 'done' keys
        """
        print(f"[DEBUG] IrisClassifierAgent processing query: '{query}'")
        
        # Check if model is trained
        if self.model is None:
            error_msg = (
                "❌ **Model Not Trained**\n\n"
                "The Iris Classifier model has not been trained yet.\n\n"
                "To train the model, run:\n"
                "```bash\n"
                "python src/agents/iris_classifier/train.py\n"
                "```\n\n"
                "This will train the model offline and save it for inference."
            )
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
            return
        
        # Parse input
        features = self.parse_input(query)
        
        if features is None:
            error_msg = (
                "❌ **Invalid Input Format**\n\n"
                "Please provide 4 feature values in one of these formats:\n\n"
                "**JSON format:**\n"
                "```json\n"
                '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}\n'
                "```\n\n"
                "**List format:**\n"
                "```\n"
                "[5.1, 3.5, 1.4, 0.2]\n"
                "```\n\n"
                "**Space or comma-separated:**\n"
                "```\n"
                "5.1 3.5 1.4 0.2\n"
                "```\n\n"
                "**Feature names:**\n"
                "- sepal_length (cm)\n"
                "- sepal_width (cm)\n"
                "- petal_length (cm)\n"
                "- petal_width (cm)\n"
            )
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
            return
        
        # Make prediction
        result = self.predict(features)
        
        # Format response
        response_parts = [
            "🌺 **Iris Flower Classification Result**\n\n",
            f"**Input Features:**\n",
            f"- Sepal Length: {features['sepal_length']} cm\n",
            f"- Sepal Width: {features['sepal_width']} cm\n",
            f"- Petal Length: {features['petal_length']} cm\n",
            f"- Petal Width: {features['petal_width']} cm\n\n",
            "---\n\n",
            f"**Predicted Class:** {result['predicted_class'].title()}\n",
            f"**Confidence:** {result['confidence']:.2%}\n\n",
            "**Class Probabilities:**\n",
        ]
        
        for class_name, prob in result['probabilities'].items():
            response_parts.append(f"- {class_name.title()}: {prob:.2%}\n")
        
        response_parts.extend([
            "\n---\n",
            "_Generated using Random Forest Classifier_\n"
        ])
        
        # Stream response
        for part in response_parts:
            yield {'content': part, 'done': False}
        
        print("[DEBUG] Response streaming complete")
        yield {'content': '', 'done': True}

