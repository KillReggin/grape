import io
from datetime import datetime
from typing import Sequence, Optional, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from app.entities.grape_cluster import GrapeCluster
from app.ports.report_port import ReportGeneratorPort
from app.ports.storage_port import StoragePort


class ReportGenerator(ReportGeneratorPort):
    def __init__(
        self,
        storage: StoragePort,
        pdf_dpi: int,
        plot_elev: int,
        plot_azim: int,
        fig_size_3d: Tuple[int, int],
        fig_size_2d: Tuple[int, int],
    ):
        self.storage = storage
        self.pdf_dpi = pdf_dpi
        self.plot_elev = plot_elev
        self.plot_azim = plot_azim
        self.fig_size_3d = fig_size_3d
        self.fig_size_2d = fig_size_2d

    def _save_fig(self, pdf, fig):
        fig.canvas.draw()
        pdf.savefig(fig, dpi=self.pdf_dpi, bbox_inches="tight")
        plt.close(fig)

    def generate(
        self,
        image_rgb,
        clusters: Sequence[GrapeCluster],
        results_dir: Optional[str] = None,
    ) -> Optional[str]:
        del results_dir

        if not clusters:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grapes_report_{timestamp}.pdf"

        buffer = io.BytesIO()
        df = pd.DataFrame([c.__dict__ for c in clusters])
        df_round = df.round(2)

        weights = df["estimated_weight_g"].values
        volumes = df["volume_px3"].values
        heights = df["height_px"].values
        upper_r = df["R_px"].values
        lower_r = df["r_px"].values
        confidences = df["confidence"].values

        norm = mpl.colors.Normalize(vmin=min(weights), vmax=max(weights))
        cmap = mpl.cm.get_cmap("coolwarm")
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)

        with PdfPages(buffer) as pdf:
            fig, ax = plt.subplots(figsize=self.fig_size_3d)
            ax.imshow(image_rgb)
            ax.axis("off")
            ax.set_title("Исходное изображение")
            self._save_fig(pdf, fig)

            fig = plt.figure(figsize=self.fig_size_3d)
            ax = fig.add_subplot(111, projection="3d")

            max_h = max(heights) * 1.2
            ax.set_zlim(0, max_h)
            ax.set_xlabel("X (px)")
            ax.set_ylabel("Y (px)")
            ax.set_zlabel("Height (px)")
            ax.set_box_aspect([1, 1, 1])

            for c in clusters:
                cx, cy = c.center_x, c.center_y
                h, upper_radius, lower_radius = c.height_px, c.R_px, c.r_px

                theta = np.linspace(0, 2 * np.pi, 30)
                z = np.linspace(0, h, 30)
                theta_grid, z_grid = np.meshgrid(theta, z)

                radius_surface = lower_radius + (upper_radius - lower_radius) * (z_grid / h)
                x = cx + radius_surface * np.cos(theta_grid)
                y = cy + radius_surface * np.sin(theta_grid)

                ax.plot_surface(
                    x,
                    y,
                    z_grid,
                    color=mappable.to_rgba(c.estimated_weight_g),
                    alpha=c.confidence * 0.6,
                    edgecolor="k",
                )

                ax.text(
                    cx,
                    cy,
                    h + 5,
                    f"{round(c.estimated_weight_g, 1)} g",
                    fontsize=8,
                    ha="center",
                )

            ax.view_init(elev=self.plot_elev, azim=self.plot_azim)
            ax.set_title("3D визуализация гроздей")

            cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=10)
            cbar.set_label("Вес грозди (g)")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=self.fig_size_2d)
            ax.hist(weights, bins=15)
            ax.set_title("Распределение веса")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=self.fig_size_2d)
            ax.scatter(volumes, weights)
            ax.set_title("Объём vs вес")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=self.fig_size_2d)
            sc = ax.scatter(lower_r, upper_r, c=weights, cmap="coolwarm")
            plt.colorbar(sc, ax=ax)
            ax.set_title("Форма гроздей")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=self.fig_size_2d)
            sc = ax.scatter(heights, weights, c=weights, cmap="viridis")
            plt.colorbar(sc, ax=ax)
            ax.set_title("Высота vs вес")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=self.fig_size_2d)
            ax.hist(confidences, bins=10)
            ax.set_title("Confidence")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.axis("off")
            ax.table(cellText=df_round.values, colLabels=df_round.columns, loc="center")
            ax.set_title("Данные по гроздям")
            self._save_fig(pdf, fig)

        buffer.seek(0)
        return self.storage.save(buffer.read(), filename)
