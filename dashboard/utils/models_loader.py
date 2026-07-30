"""Cached ML model loaders for dashboard pages."""
from __future__ import annotations

import os

import streamlit as st


@st.cache_resource
def load_clean_dirty_model():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    import tensorflow as tf

    model_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "clean_dirty_model.h5")
    )
    if not os.path.exists(model_path):
        model_path = "artifacts/clean_dirty_model.h5"
    return tf.keras.models.load_model(model_path)


@st.cache_resource
def load_yolo_model():
    from ultralytics import YOLO

    model_path = os.path.abspath(
        "yolo_fault_detection/runs/runs/detect/train/weights/best.pt"
    )
    return YOLO(model_path)
