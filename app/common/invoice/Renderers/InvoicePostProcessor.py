import math
import random
from tkinter import Image

import numpy as np
from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX
from common.view.components.BoundingBoxLayer import Drawable
from common.invoice.models.Invoice import Invoice
from PIL import Image, ImageOps, ImageFilter, ImageDraw


class InvoicePostProcessor:
    

    def __init__(self):
        ...

    def post_process(self, invoice: Invoice) -> bool:
        self._apply_random_rotation(invoice)
        self._apply_visual_effects(invoice)
        self._apply_random_translation(invoice)

        return True

    # =========================
    # GEOMETRICKÉ TRANSFORMACE
    # =========================

    def _apply_random_rotation(self, invoice: Invoice) -> None:
        if random.random() >= 0.4:
            return

        angle_deg = random.randint(-2, 2)
        if angle_deg == 0:
            return

        original_w, original_h = invoice.image.size

        rotated_img = invoice.image.rotate(
            angle_deg,
            expand=True,
            fillcolor=(255, 255, 255),
            resample=Image.Resampling.BICUBIC,
        )

        rotation_matrix = self._build_rotation_expand_matrix(
            width=original_w,
            height=original_h,
            angle_deg=angle_deg,
        )
        self._apply_matrix(invoice, rotation_matrix)

        rotated_w, rotated_h = rotated_img.size
        scale_w = float(_A4_W_PX) / rotated_w
        scale_h = float(_A4_H_PX) / rotated_h

        scale_matrix = np.array([
            [scale_w, 0, 0],
            [0, scale_h, 0],
            [0, 0, 1],
        ], dtype=float)

        self._apply_matrix(invoice, scale_matrix)

        invoice.image = rotated_img.resize(
            (_A4_W_PX, _A4_H_PX),
            resample=Image.Resampling.BICUBIC,
        )

    def _apply_random_translation(self, invoice: Invoice) -> None:
        if random.random() >= 0.4:
            return

        tx = random.random() * 50
        ty = random.random() * 50

        translated_img = invoice.image.transform(
            invoice.image.size,
            Image.AFFINE,
            (1, 0, -tx, 0, 1, -ty),
            fillcolor=(255, 255, 255),
        )

        translation_matrix = np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1],
        ], dtype=float)

        self._apply_matrix(invoice, translation_matrix)
        invoice.image = translated_img

    def _build_rotation_expand_matrix(self, width: int, height: int, angle_deg: float) -> np.ndarray:
        """
        Vrátí homogenní matici, která odpovídá rotaci obrazu kolem středu
        včetně offsetu vzniklého při expand=True.
        """
        cx, cy = width / 2.0, height / 2.0
        theta = math.radians(-angle_deg)

        t1 = np.array([
            [1, 0, -cx],
            [0, 1, -cy],
            [0, 0, 1],
        ], dtype=float)

        r = np.array([
            [math.cos(theta), -math.sin(theta), 0],
            [math.sin(theta),  math.cos(theta), 0],
            [0, 0, 1],
        ], dtype=float)

        t2c = np.array([
            [1, 0, cx],
            [0, 1, cy],
            [0, 0, 1],
        ], dtype=float)

        m_center = t2c @ r @ t1

        corners = np.array([
            [0, width, width, 0],
            [0, 0, height, height],
            [1, 1, 1, 1],
        ], dtype=float)

        transformed_corners = m_center @ corners
        offset_x = -transformed_corners[0, :].min()
        offset_y = -transformed_corners[1, :].min()

        t_offset = np.array([
            [1, 0, offset_x],
            [0, 1, offset_y],
            [0, 0, 1],
        ], dtype=float)

        return t_offset @ m_center

    # =========================
    # VIZUÁLNÍ EFEKTY
    # =========================

    def _apply_visual_effects(self, invoice:Invoice) -> None:
        self._maybe_grayscale(invoice)
        self._maybe_blur(invoice)
        self._maybe_salt_and_pepper_noise(invoice)
        self._maybe_yellow_paper(invoice)
        self._maybe_scratches(invoice)
        self._maybe_grayscale(invoice)


    def _maybe_grayscale(self, invoice: Invoice) -> None:
        if random.random() < 0.3:
            invoice.image = ImageOps.grayscale(invoice.image).convert("RGB")

    def _maybe_blur(self, invoice:Invoice) -> None:
        if random.random() < 0.3:
            invoice.image = invoice.image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.1, 0.5)))

    def _maybe_salt_and_pepper_noise(self, invoice:Invoice) -> None:
        arr = np.array(invoice.image)
        amount = random.uniform(0.00005, 0.0002)

        noise = np.random.choice(
            [0, 255],
            arr.shape,
            p=[1 - amount, amount]
        ).astype(np.uint8)

        mask = np.random.rand(*arr.shape[:2]) < amount
        arr[mask] = noise[mask]

        invoice.image = Image.fromarray(arr)

    def _maybe_yellow_paper(self, invoice: Invoice) -> None:
        if random.random() < 0.25:
            overlay = Image.new("RGB", invoice.image.size, (240, 230, 200))
            invoice.image = Image.blend(invoice.image, overlay, 0.08)

    def _maybe_scratches(self, invoice:Invoice) -> None:
        if random.random() >= 0.2:
            return 

        draw = ImageDraw.Draw(invoice.image)
        for _ in range(random.randint(1, 3)):
            x1, y1 = random.randint(0, invoice.image.width), random.randint(0, invoice.image.height)
            x2, y2 = random.randint(0, invoice.image.width), random.randint(0, invoice.image.height)
            draw.line(
                (x1, y1, x2, y2),
                fill=(150, 150, 150),
                width=random.randint(1, 3),
            )

    # =========================
    # BBOX TRANSFORMACE
    # =========================

    def _apply_matrix(self, invoice: Invoice, matrix: np.ndarray) -> None:
        self._transform_bbox_collection(invoice._tokens, matrix)
        self._transform_bbox_collection(invoice._spans, matrix)
        self._transform_bbox_collection(invoice._segments, matrix)

    def _transform_bbox_collection(self, items: list[Drawable], matrix: np.ndarray) -> None:
        for item in items:
            item.b_box = self._transform_bbox(item.b_box, matrix)

    def _transform_bbox(self, bbox, matrix: np.ndarray):
        left, top, right, bottom = bbox

        points = np.array([
            [left, top, 1.0],
            [right, top, 1.0],
            [right, bottom, 1.0],
            [left, bottom, 1.0],
        ], dtype=float).T

        transformed_points = matrix @ points
        xs = transformed_points[0, :]
        ys = transformed_points[1, :]

        return (
            float(xs.min()),
            float(ys.min()),
            float(xs.max()),
            float(ys.max()),
        )