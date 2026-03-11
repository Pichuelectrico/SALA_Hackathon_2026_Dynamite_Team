# Rainfall Prediction System - Hackaton SALA

This project implements a localized, two-stage machine learning system designed to predict rainfall occurrence and intensity. The architecture is composed of a classification model and a regression model that work in tandem to evaluate real-time or historical environmental variables to predict rain within the next hour.

## 🏗️ Project Architecture & Data Pipeline

The data pipeline and modeling logic revolve around predicting localized heavy rain events efficiently.

1. **Data Cleaning & Splitting (`limpieza.py`)**: 
   - Reads the raw station features dataset.
   - Splits data temporally into Train (70%), Validation (15%), and Test (15%) sets to prevent data leakage and simulate real-time forecasting.
   - Generates two targeted datasets:
     - **Occurrence Dataset**: Contains all samples with target labels indicating if rain occurs (>0 mm).
     - **Intensity Dataset**: Contains only samples where rain actually occurred, focusing purely on predicting the amount of rain (mm).

## 🤖 Models Overview

The core of the prediction lies in the two-stage model architecture (found in scripts like `train_two_stage_model.py` and `build_option3_hybrid.py`):

*   **Stage 1: Classification (Occurrence)**
    *   **Model**: `HistGradientBoostingClassifier`
    *   **Objective**: Compute the probability of a rain event within the next hour.
    *   **Thresholding**: Employs an optimal F1 score thresholding mechanism on the validation set to accurately separate positive and negative predictions.
*   **Stage 2: Regression (Intensity)**
    *   **Model**: `HistGradientBoostingRegressor`
    *   **Objective**: Predict the specific volume of rain (in mm), trained strictly on periods where rain actually happened.
*   **Combined Gated Output**:
    *   The regressor's output is *gated* by the classifier. The final predicted intensity is zero if the classifier predicts no rain, otherwise, it allows the regressor's output through.

Both stage models use preprocessing pipelines (handling imputation and one-hot encoding for categorical variables) and are serialized using `joblib`.

## 📊 Evaluation and Testing

The model performances are recorded as JSON metrics during training:
*   **Classifier Evaluators**: Test ROC AUC, PR AUC, and F1 Score measure how well the model acts as an alerting mechanism.
*   **Regressor Evaluators**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) determine the intensity tracking accuracy.
*   **Joint Two-Stage Metrics**: "Expected" (Expected Value formulation) vs. "Gated" (Hard Threshold formulation) intensity errors evaluate the unified hybrid system.

All models and their specific prediction snapshots are dumped into `output/models/`.

## ⚙️ Setup and Installation

Follow these steps to set up the runtime environment and execute the visualization tool. Ensure you have Python 3 installed.

1. **Activate the Virtual Environment**:
   A Python virtual environment (`env`) has been prepared. Activate it using:
   ```bash
   source env/bin/activate
   ```
   *(For Windows use `env\Scripts\activate`)*

2. **Install Requirements**:
   Install the dependent packages via `pip`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Running the Frontend**:
   The frontend visualization reads directly from the compiled output datasets. Run the following command from the root directory:
   ```bash
   python frontend/Visualizacion_SALA.py
   ```
   This will generate visualization PNGs (like feature importance, metrics, real vs predicted plots) straight into your directory.
