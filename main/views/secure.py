import os
import io
import fitz
from PyPDF2 import PdfReader, PdfWriter
from django.shortcuts import get_object_or_404, render, redirect
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings

from ..models import Thesis, Submission
from authapp.models import Profile

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

@login_required
def view_thesis(request, thesis_id):
    try:
        thesis = Thesis.objects.get(pk=thesis_id)
    except Thesis.DoesNotExist:
        thesis = get_object_or_404(Submission, pk=thesis_id)
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        messages.error(request, "Full document access restricted.")
        return redirect('thesis_detail', pk=thesis_id)
    if not thesis.file or not os.path.exists(thesis.file.path):
        raise Http404()
    doc = fitz.open(thesis.file.path)
    total_pages = doc.page_count
    doc.close()
    return render(request, 'main/secure_viewer.html', {'thesis_id': thesis_id, 'total_pages': range(1, total_pages + 1), 'query': request.GET.get('q', '')})

@login_required
def serve_thesis_page_image(request, thesis_id, page_num):
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        return HttpResponseForbidden("Not authorized to view full document.")
    try:
        try:
            thesis = Thesis.objects.get(pk=thesis_id)
        except Exception:
            thesis = get_object_or_404(Submission, pk=thesis_id)
        doc = fitz.open(thesis.file.path)
        page = doc.load_page(int(page_num) - 1)
        q = request.GET.get('q', '').strip()
        if q:
            for quad in page.search_for(q, quads=True):
                h = page.add_highlight_annot(quad)
                h.set_colors(stroke=[1, 1, 0])
                h.update()
        watermark_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'watermark.png')
        if os.path.exists(watermark_path):
            page.insert_image(page.rect, filename=watermark_path, keep_proportion=True, overlay=False)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        res = HttpResponse(pix.tobytes("png"), content_type="image/png")
        doc.close()
        return res
    except Exception:
        raise Http404()

@login_required
@user_passes_test(lambda u: u.is_staff)
def view_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        return HttpResponseForbidden()
    return FileResponse(thesis.file.open('rb'), content_type='application/pdf')

@login_required
def view_thesis_file_highlight(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        return HttpResponseForbidden()
    q = request.GET.get('q', '').strip()
    if not q:
        return view_thesis_file(request, pk)
    doc = fitz.open(thesis.file.path)
    for p in doc:
        for r in p.search_for(q):
            a = p.add_highlight_annot(r)
            a.update()
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='application/pdf')

def download_thesis_file(request, pk):
    return HttpResponseForbidden("Downloading is prohibited.")

@login_required
def restricted_view_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404()
    pdf_reader = PdfReader(thesis.file.open('rb'))
    pdf_writer = PdfWriter()
    for i in range(min(3, len(pdf_reader.pages))):
        pdf_writer.add_page(pdf_reader.pages[i])
    buf = io.BytesIO()
    pdf_writer.write(buf)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='application/pdf')
