import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages

from app.ports.report_port import ReportGeneratorPort
from app.ports.storage_port import StoragePort
from app.config import Config


class ReportGenerator(ReportGeneratorPort):

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _save_fig(self, pdf, fig):
        fig.canvas.draw()
        pdf.savefig(fig, dpi=Config.PDF_DPI, bbox_inches='tight')
        plt.close(fig)

    def generate(self, image_rgb, clusters, results_dir=None):

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

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_3D)
            ax.imshow(image_rgb)
            ax.axis("off")
            ax.set_title("Исходное изображение")
            self._save_fig(pdf, fig)

            fig = plt.figure(figsize=Config.FIG_SIZE_3D)
            ax = fig.add_subplot(111, projection='3d')

            max_h = max(heights) * 1.2
            ax.set_zlim(0, max_h)

            ax.set_xlabel('X (px)')
            ax.set_ylabel('Y (px)')
            ax.set_zlabel('Height (px)')

            ax.set_box_aspect([1, 1, 1])

            for c in clusters:

                cx, cy = c.center_x, c.center_y
                h, R, r = c.height_px, c.R_px, c.r_px

                theta = np.linspace(0, 2*np.pi, 30)
                z = np.linspace(0, h, 30)
                Theta, Z = np.meshgrid(theta, z)

                R_surface = r + (R - r) * (Z / h)

                X = cx + R_surface * np.cos(Theta)
                Y = cy + R_surface * np.sin(Theta)

                ax.plot_surface(
                    X, Y, Z,
                    color=mappable.to_rgba(c.estimated_weight_g),
                    alpha=c.confidence * 0.6,
                    edgecolor='k'
                )

                ax.text(
                    cx, cy, h + 5,
                    f"{round(c.estimated_weight_g,1)} g",
                    fontsize=8,
                    ha='center'
                )

            ax.view_init(elev=Config.PLOT_ELEV, azim=Config.PLOT_AZIM)
            ax.set_title("3D визуализация гроздей")

            cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=10)
            cbar.set_label("Вес грозди (g)")

            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_2D)
            ax.hist(weights, bins=15)
            ax.set_title("Распределение веса")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_2D)
            ax.scatter(volumes, weights)
            ax.set_title("Объём vs вес")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_2D)
            sc = ax.scatter(lower_r, upper_r, c=weights, cmap='coolwarm')
            plt.colorbar(sc, ax=ax)
            ax.set_title("Форма гроздей")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_2D)
            sc = ax.scatter(heights, weights, c=weights, cmap='viridis')
            plt.colorbar(sc, ax=ax)
            ax.set_title("Высота vs вес")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=Config.FIG_SIZE_2D)
            ax.hist(confidences, bins=10)
            ax.set_title("Confidence")
            self._save_fig(pdf, fig)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.axis('off')

            ax.table(
                cellText=df_round.values,
                colLabels=df_round.columns,
                loc='center'
            )

            ax.set_title("Данные по гроздям")

            self._save_fig(pdf, fig)

        buffer.seek(0)

        return self.storage.save(buffer.read(), filename)