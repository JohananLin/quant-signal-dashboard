import pandas as pd
import numpy as np
from utils.data import get_hist_data_baostock   # 如果报错，确保运行路径正确
from strategies.feature_engineering import create_features, FEATURE_COLS
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')