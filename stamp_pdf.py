#!/usr/bin/env python3
import argparse, fitz, os, sys

def add_initials(doc, initials_path, width_pts=72, margin_pts=12):
    pix = fitz.Pixmap(initials_path)
    ratio = pix.height / pix.width
    w = float(width_pts)
    h = w * ratio
    for page in doc:
        pr = page.rect
        # bottom-right placement
        x = pr.width - w - float(margin_pts)
        y = pr.height - h - float(margin_pts)
        page.insert_image(
            fitz.Rect(x, y, x + w, y + h),
            filename=initials_path,
            keep_proportion=True,
            overlay=True
        )

def add_signature(doc, signature_path, page_num=None, x=None, y=None, width_pts=180):
    if page_num is None or x is None or y is None:
        return
    page = doc.load_page(int(page_num))
    pix = fitz.Pixmap(signature_path)
    ratio = pix.height / pix.width
    w = float(width_pts)
    h = w * ratio
    page.insert_image(
        fitz.Rect(float(x), float(y), float(x) + w, float(y) + h),
        filename=signature_path,
        keep_proportion=True,
        overlay=True
    )

def main():
    p = argparse.ArgumentParser(description="Stamp initials on each PDF page (bottom-right). Optional manual signature placement.")
    p.add_argument("input_pdf")
    p.add_argument("output_pdf")
    p.add_argument("--initials", required=True, help="Path to initials PNG")
    p.add_argument("--signature", help="Path to full-signature PNG")
    p.add_argument("--sig-page", type=int, help="Page number (0-based) for signature placement")
    p.add_argument("--sig-x", type=float, help="X coordinate (points) for signature left edge")
    p.add_argument("--sig-y", type=float, help="Y coordinate (points) for signature top edge")
    p.add_argument("--initials-width", type=float, default=72, help="Initials width (pts). Default 72")
    p.add_argument("--initials-margin", type=float, default=12, help="Margin from edges (pts). Default 12")
    p.add_argument("--signature-width", type=float, default=180, help="Signature width (pts). Default 180")
    p.add_argument("--fullsig", help="Signature coordinates as 'XxY' in points (e.g. 548x300)")
    p.add_argument("--onpage", type=int, help="1-based page number for signature (default: last page)")
    args = p.parse_args()

    if not os.path.isfile(args.input_pdf) or not os.path.isfile(args.initials):
        print("Input PDF or initials PNG not found.", file=sys.stderr); sys.exit(1)
    if args.signature and not os.path.isfile(args.signature):
        print("Signature PNG not found.", file=sys.stderr); sys.exit(1)

    doc = fitz.open(args.input_pdf)

    # Place initials everywhere
    add_initials(doc, args.initials, args.initials_width, args.initials_margin)

    # Map convenience flags to signature placement
    if args.fullsig:
        try:
            sx, sy = args.fullsig.lower().split("x")
            args.sig_x = float(sx)
            args.sig_y = float(sy)
        except Exception:
            print("Invalid --fullsig. Use XxY, e.g. 548x300", file=sys.stderr); sys.exit(2)

    if args.onpage is not None:
        args.sig_page = int(args.onpage) - 1  # user supplies 1-based page

    if args.signature and args.sig_page is None:
        args.sig_page = len(doc) - 1  # default to last page

    if args.signature:
        add_signature(doc, args.signature, args.sig_page, args.sig_x, args.sig_y, args.signature_width)

    doc.save(args.output_pdf, deflate=True)
    doc.close()

if __name__ == "__main__":
    main()
