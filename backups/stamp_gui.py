#!/usr/bin/env python3
import sys, fitz, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton,
    QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QRectF

# ---------- Draggable preview rectangle ----------
class DragRect(QGraphicsRectItem):
    def __init__(self, x, y, w, h, tag="sig", on_activate=None, page_index=0):
        super().__init__(x, y, w, h)
        self.tag = tag
        self.on_activate = on_activate
        self.page_index = page_index
        self.preview_item = None     # QGraphicsPixmapItem child
        self.source_path = None      # chosen image file path

        self.setBrush(QBrush(QColor(0, 0, 0, 60)))
        self.setPen(QPen(QColor(0, 0, 0, 180), 2, Qt.DashLine))
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )

    def set_preview(self, img_path):
        if not img_path or not os.path.isfile(img_path):
            return
        self.source_path = img_path
        pm = QPixmap(img_path)
        if pm.isNull():
            return
        r = self.rect()
        scaled = pm.scaled(int(r.width()), int(r.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        xoff = (r.width() - scaled.width()) / 2.0
        yoff = (r.height() - scaled.height()) / 2.0
        if self.preview_item:
            self.preview_item.setPixmap(scaled)
            self.preview_item.setPos(r.x() + xoff, r.y() + yoff)
        else:
            self.preview_item = QGraphicsPixmapItem(scaled, parent=self)
            self.preview_item.setZValue(11)
            self.preview_item.setPos(r.x() + xoff, r.y() + yoff)

    def mouseReleaseEvent(self, ev):
        if self.preview_item:
            r = self.rect()
            pm = self.preview_item.pixmap()
            xoff = (r.width() - pm.width()) / 2.0
            yoff = (r.height() - pm.height()) / 2.0
            self.preview_item.setPos(r.x() + xoff, r.y() + yoff)
        r = self.rect().translated(self.pos())
        print("BOX", self.tag, "PG", self.page_index, "PX", int(r.x()), int(r.y()), int(r.width()), int(r.height()))
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if callable(self.on_activate):
            self.on_activate(self.tag)
        super().mouseDoubleClickEvent(ev)


# ---------- PDF viewer ----------
class PDFViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.doc = None
        self.pdf_path = None
        self.page_index = 0
        self.image_item = None
        self.rects = []  # DragRect overlays

        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def page_count(self):
        return 0 if not self.doc else len(self.doc)

    def go_first(self):
        if self.doc: self.show_page(0)

    def go_last(self):
        if self.doc: self.show_page(len(self.doc) - 1)

    def next_page(self):
        if self.doc and self.page_index + 1 < len(self.doc):
            self.show_page(self.page_index + 1)

    def prev_page(self):
        if self.doc and self.page_index - 1 >= 0:
            self.show_page(self.page_index - 1)

    def load_pdf(self, path):
        self.pdf_path = path
        self.doc = fitz.open(path)
        self.show_page(0)

    def show_page(self, index):
        if not self.doc: return
        if index < 0 or index >= len(self.doc): return
        self.page_index = index

        page = self.doc.load_page(index)
        pix = page.get_pixmap()
        if pix.alpha:
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888)
        else:
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        qpix = QPixmap.fromImage(img)

        if self.image_item:
            self.scene.removeItem(self.image_item)
        self.image_item = QGraphicsPixmapItem(qpix)
        self.scene.addItem(self.image_item)

        self.setSceneRect(self.image_item.boundingRect())
        self.fitInView(self.image_item, Qt.KeepAspectRatio)

        # show signature rects only on their own page; others stay visible
        for r in self.rects:
            if isinstance(r, DragRect):
                if r.tag == "signature":
                    r.setVisible(r.page_index == self.page_index)
                else:
                    r.setVisible(True)

    def add_drag_rect(self, w=180, h=60, tag="sig", on_activate=None):
        if not self.image_item: return None
        r = DragRect(20, 20, w, h, tag, on_activate, page_index=self.page_index)
        r.setZValue(10)
        self.scene.addItem(r)
        self.rects.append(r)
        # visibility rule on creation
        if tag == "signature":
            r.setVisible(r.page_index == self.page_index)
        return r

    def remove_rects_by_tag(self, tag):
        to_remove = [r for r in self.rects if getattr(r, "tag", None) == tag]
        for r in to_remove:
            if r.scene() is self.scene:
                self.scene.removeItem(r)
            try:
                self.rects.remove(r)
            except ValueError:
                pass
        self.scene.update()
        self.viewport().update()


# ---------- Main window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Stamper")
        self.resize(1000, 1000)

        self.viewer = PDFViewer()

        # chosen files
        self.initials_path = None
        self.signature_path = None
        self.other_stamp_path = None

        # buttons
        self.open_btn = QPushButton("Open PDF")
        self.open_btn.clicked.connect(self.open_pdf)

        self.first_btn = QPushButton("≪"); self.first_btn.setToolTip("First page"); self.first_btn.clicked.connect(self.viewer.go_first)
        self.prev_btn  = QPushButton("‹");  self.prev_btn.setToolTip("Previous page"); self.prev_btn.clicked.connect(self.viewer.prev_page)
        self.next_btn  = QPushButton("›");  self.next_btn.setToolTip("Next page"); self.next_btn.clicked.connect(self.viewer.next_page)
        self.last_btn  = QPushButton("≫"); self.last_btn.setToolTip("Last page"); self.last_btn.clicked.connect(self.viewer.go_last)

        self.add_initials_btn = QPushButton("Add initials (all pages)")
        self.add_initials_btn.clicked.connect(self.choose_initials)

        self.add_fullsig_btn = QPushButton("Add full signature")
        self.add_fullsig_btn.clicked.connect(self.choose_fullsig)

        self.add_other_btn = QPushButton("Add other stamp")
        self.add_other_btn.setToolTip("like a QR code or watermark")
        self.add_other_btn.clicked.connect(self.choose_other)

        self.remove_sig_btn  = QPushButton("Remove signature"); self.remove_sig_btn.clicked.connect(lambda: self.remove_tag("signature"))
        self.remove_init_btn = QPushButton("Remove initials");  self.remove_init_btn.clicked.connect(lambda: self.remove_tag("initials"))
        self.remove_other_btn= QPushButton("Remove other stamps"); self.remove_other_btn.clicked.connect(lambda: self.remove_tag("other"))

        self.save_btn = QPushButton("Save as…")
        self.save_btn.clicked.connect(self.save_stamped_pdf)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.viewer)

        btns = QHBoxLayout()
        for b in (self.open_btn, self.first_btn, self.prev_btn, self.next_btn, self.last_btn,
                  self.add_initials_btn, self.add_fullsig_btn, self.add_other_btn,
                  self.remove_init_btn, self.remove_sig_btn, self.remove_other_btn,
                  self.save_btn):
            btns.addWidget(b)
        layout.addLayout(btns)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ---------- helpers ----------
    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            self.viewer.load_pdf(path)
            print("OPEN_PDF", path)

    def choose_image_file(self, title):
        p, _ = QFileDialog.getOpenFileName(self, title, "", "Image Files (*.png *.jpg *.jpeg)")
        return p if p and os.path.isfile(p) else None

    def choose_initials(self):
        p = self.choose_image_file("Choose initials image")
        if p:
            self.initials_path = p
            print("INITIALS_SET", p)
            rect = self.viewer.add_drag_rect(72, 48, "initials", on_activate=self.activate_box)
            if rect: rect.set_preview(p)

    def choose_fullsig(self):
        p = self.choose_image_file("Choose full signature image")
        if p:
            self.signature_path = p
            print("FULLSIG_SET", p)
            rect = self.viewer.add_drag_rect(180, 60, "signature", on_activate=self.activate_box)
            if rect: rect.set_preview(p)

    def choose_other(self):
        p = self.choose_image_file("Choose other stamp image")
        if p:
            self.other_stamp_path = p
            print("OTHER_STAMP_SET", p)
            rect = self.viewer.add_drag_rect(120, 120, "other", on_activate=self.activate_box)
            if rect: rect.set_preview(p)

    def activate_box(self, tag):
        if tag == "initials":
            p = self.choose_image_file("Choose initials image")
            if p:
                self.initials_path = p
                print("INITIALS_SET", p)
                for r in list(self.viewer.rects):
                    if isinstance(r, DragRect) and r.tag == "initials":
                        r.set_preview(self.initials_path)
        elif tag == "signature":
            p = self.choose_image_file("Choose full signature image")
            if p:
                self.signature_path = p
                print("FULLSIG_SET", p)
                for r in list(self.viewer.rects):
                    if isinstance(r, DragRect) and r.tag == "signature":
                        r.set_preview(self.signature_path)
        elif tag == "other":
            p = self.choose_image_file("Choose other stamp image")
            if p:
                self.other_stamp_path = p
                print("OTHER_STAMP_SET", p)
                for r in list(self.viewer.rects):
                    if isinstance(r, DragRect) and r.tag == "other":
                        r.set_preview(self.other_stamp_path)

    def remove_tag(self, tag):
        if tag == "initials":
            self.initials_path = None
        elif tag == "signature":
            self.signature_path = None
        elif tag == "other":
            self.other_stamp_path = None
        self.viewer.remove_rects_by_tag(tag)
        print("REMOVED_TAG", tag)

    # ---------- stamping / saving ----------
    def save_stamped_pdf(self):
        if not self.viewer.doc or not self.viewer.pdf_path:
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "Save stamped PDF", "", "PDF Files (*.pdf)")
        if not out_path:
            return

        doc = fitz.open(self.viewer.pdf_path)

        def map_rect_to_page(rect_item: DragRect, target_page_idx: int):
            src_page_idx = rect_item.page_index
            src_page = doc.load_page(src_page_idx)
            tgt_page = doc.load_page(target_page_idx)
            src_pix = src_page.get_pixmap()
            tgt_pix = tgt_page.get_pixmap()

            r_scene: QRectF = rect_item.rect().translated(rect_item.pos())
            x_norm = r_scene.x() / float(src_pix.width)
            y_norm = r_scene.y() / float(src_pix.height)
            w_norm = r_scene.width() / float(src_pix.width)
            h_norm = r_scene.height() / float(src_pix.height)

            tgt_rect = tgt_page.rect
            x_pts = x_norm * tgt_rect.width
            y_pts = y_norm * tgt_rect.height
            w_pts = w_norm * tgt_rect.width
            h_pts = h_norm * tgt_rect.height
            return (tgt_page, fitz.Rect(x_pts, y_pts, x_pts + w_pts, y_pts + h_pts))

        # initials: apply to all pages (if placed once)
        initials_rects = [r for r in self.viewer.rects if r.tag == "initials" and self.initials_path]
        initials_src = initials_rects[0] if initials_rects else None
        if initials_src and os.path.isfile(self.initials_path):
            for i in range(len(doc)):
                page, rect_pts = map_rect_to_page(initials_src, i)
                page.insert_image(rect_pts, filename=self.initials_path, keep_proportion=True, overlay=True)

        # signature & other: only on pages where placed
        if self.signature_path and os.path.isfile(self.signature_path):
            for r in [r for r in self.viewer.rects if r.tag == "signature"]:
                page, rect_pts = map_rect_to_page(r, r.page_index)
                page.insert_image(rect_pts, filename=self.signature_path, keep_proportion=True, overlay=True)

        if self.other_stamp_path and os.path.isfile(self.other_stamp_path):
            for r in [r for r in self.viewer.rects if r.tag == "other"]:
                page, rect_pts = map_rect_to_page(r, r.page_index)
                page.insert_image(rect_pts, filename=self.other_stamp_path, keep_proportion=True, overlay=True)

        doc.save(out_path, deflate=True)
        doc.close()
        print("SAVED", out_path)


# ---------- run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
