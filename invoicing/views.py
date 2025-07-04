from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from User.models import UserSession
from .models import *
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views import View
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from io import BytesIO
import json
from decimal import Decimal
from reportlab.lib.styles import getSampleStyleSheet
from django.core.files.base import ContentFile
from urllib.parse import quote
import qrcode
from django.shortcuts import redirect
from datetime import datetime
import base64
# Create your views here.

import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_POST

# Configure logger
logger = logging.getLogger(__name__)

class CompaniesView(TemplateView):
    template_name = 'invoicing/companies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        return context

class CreateCompanyView(TemplateView):
    template_name = 'invoicing/create_company.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger.debug("Rendering create company form")
        return context

    def post(self, request, *args, **kwargs):
        logger.debug("Processing company creation request")
        try:

            user_session_id = request.session.get('user_session_id')
            if not user_session_id:
                return JsonResponse({'success': False, 'message': 'User not authenticated'}, status=401)
            
            try:
                user_session = UserSession.objects.get(id=user_session_id)
                user = user_session.user
                user_id = user.user_id
            except UserSession.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid session'}, status=401)
            
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                print("User does not exist")
            # Get form data
            company_name = request.POST.get('company_name')
            company_logo = request.FILES.get('company_logo')
            company_gst_number = request.POST.get('company_gst_number')
            company_mobile_number = request.POST.get('company_mobile_number')
            company_email = request.POST.get('company_email')
            company_signature = request.FILES.get('company_signature')
            company_invoice_prefix = request.POST.get('company_invoice_prefix')
            company_bank_name = request.POST.get('company_bank_name')
            company_bank_account_number = request.POST.get('company_bank_account_number')
            company_bank_ifsc_code = request.POST.get('company_bank_ifsc_code')
            company_upi_id = request.POST.get('company_upi_id')
            company_address = request.POST.get('company_address')
            company_state = request.POST.get('company_state')

            logger.debug(f"Received company data: name={company_name}, email={company_email}, state={company_state}")
            logger.debug(f"Files received: logo={bool(company_logo)}, signature={bool(company_signature)}")

            # Create company
            logger.debug("Creating company record")
            company = Company.objects.create(
                user=user,
                company_name=company_name,
                company_logo=company_logo,
                company_gst_number=company_gst_number,
                company_mobile_number=company_mobile_number,
                company_email=company_email,
                company_signature=company_signature,
                company_invoice_prefix=company_invoice_prefix,
                company_bank_name=company_bank_name,
                company_bank_account_number=company_bank_account_number,
                company_bank_ifsc_code=company_bank_ifsc_code,
                company_upi_id=company_upi_id,
                company_address=company_address,
                company_state=company_state
            )

            logger.info(f"Company '{company_name}' created successfully")
            return JsonResponse({
                'success': True,
                'redirect_url': '/invoicing/companies/'
            })

        except Exception as e:
            logger.error(f"Error creating company: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': str(e)
            }, status=400)

class EditCompanyView(View):
    def get(self, request, company_id):
        try:
            company = Company.objects.get(company_id=company_id)
            context = {
                'company': company,
            }
            return render(request, 'invoicing/edit_company.html', context)
        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving company: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, company_id):
        try:
            company = Company.objects.get(company_id=company_id)

            # Update company fields
            company.company_name = request.POST.get('company_name')
            if 'company_logo' in request.FILES:
                company.company_logo = request.FILES['company_logo']
            company.company_gst_number = request.POST.get('company_gst_number')
            company.company_mobile_number = request.POST.get('company_mobile_number')
            company.company_email = request.POST.get('company_email')
            if 'company_signature' in request.FILES:
                company.company_signature = request.FILES['company_signature']
            company.company_invoice_prefix = request.POST.get('company_invoice_prefix')
            company.company_bank_name = request.POST.get('company_bank_name')
            company.company_bank_account_number = request.POST.get('company_bank_account_number')
            company.company_bank_ifsc_code = request.POST.get('company_bank_ifsc_code')
            company.company_upi_id = request.POST.get('company_upi_id')
            company.company_address = request.POST.get('company_address')
            company.company_state = request.POST.get('company_state')

            company.save()
            logger.info(f"Company '{company.company_name}' updated successfully")

            return JsonResponse({
                'success': True,
                'redirect_url': '/invoicing/companies/'
            })

        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            logger.error(f"Error updating company: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=400)

class DeleteCompanyView(View):
    def post(self, request, company_id):
        try:
            company = Company.objects.get(company_id=company_id)
            company_name = company.company_name
            
            # Delete associated files
            if company.company_logo:
                company.company_logo.delete()
            if company.company_signature:
                company.company_signature.delete()
                
            company.delete()
            logger.info(f"Company '{company_name}' deleted successfully")

            return JsonResponse({
                'success': True,
                'message': 'Company deleted successfully'
            })

        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting company: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CreateInvoiceView(TemplateView):
    template_name = 'invoicing/create_invoice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_session_id = self.request.session.get('user_session_id')
        if not user_session_id:
            logger.warning("User not authenticated in CreateInvoiceView")
            # We can't return JsonResponse in get_context_data, so we'll handle this in the template
            context['authenticated'] = False
            return context
        
        try:
            user_session = UserSession.objects.get(id=user_session_id)
            user = user_session.user
            user_id = user.user_id
            context['authenticated'] = True
            context['user'] = user
        except UserSession.DoesNotExist:
            logger.warning("Invalid session in CreateInvoiceView")
            context['authenticated'] = False
            return context
        
        try:
            user = User.objects.get(user_id=user_id)
            context['user_details'] = user
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist")
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        context['products'] = Product.objects.all()
        context['STATE_CHOICES'] = STATE_CHOICES  # Add STATE_CHOICES to the context
        logger.debug("Rendering create invoice form")
        return context
    
    @staticmethod
    def generate_upi_link(company, final_total):
        try:
            # Properly URL encode parameters
            company_name = quote(company.company_name, safe='')
            upi_id = quote(company.company_upi_id, safe='')
            
            # Format amount to remove decimal and leading zeros
            upi_amount = f"{final_total:.2f}".replace('.', '')
            upi_amount = upi_amount.lstrip('0')  # Remove leading zeros
            
            # Create a more universal UPI link format
            upi_link = (
                f"upi://pay?"
                f"pa={upi_id}&"
                f"pn={company_name}&"
                f"am={upi_amount}&"
                f"cu=INR&"
                f"tn={quote('Invoice Payment', safe='')}"
            )
        
            return upi_link
        except Exception as e:
            logger.error(f"Error generating UPI link: {str(e)}")
            return None

    def generate_pdf(self, request):
        try:
            # Get data from request
            data = json.loads(request.body)
            logger.info(f"Received data for PDF generation: {data}")

            company_id = data.get('company_id')
            bill_type = data.get('bill_type')
            billing_details = data.get('billing_details', {})
            shipping_details = data.get('shipping_details', {})
            products = data.get('products', [])

            # Validate data
            if not all([company_id, bill_type, billing_details, products]):
                logger.error("Missing required data")
                return JsonResponse({'error': 'Missing required data'}, status=400)

            try:
                company = Company.objects.get(company_id=company_id)
            except Company.DoesNotExist:
                logger.error(f"Company not found: {company_id}")
                return JsonResponse({'error': 'Company not found'}, status=404)

            # Create billing record
            try:
                billing = Billing.objects.create(
                    company=company,
                    billing_name=billing_details['name'],
                    billing_email=billing_details['email'],
                    billing_phone=billing_details['mobile'],
                    billing_gst_number=billing_details['gstin'],
                    billing_address=billing_details['address'],
                    billing_state=billing_details['state']
                )
            except Exception as e:
                logger.error(f"Error creating billing: {str(e)}")
                return JsonResponse({'error': 'Error creating billing record'}, status=400)

            # Calculate total amount
            total_amount = sum(Decimal(str(product['total'])) for product in products)

            # Create invoice record
            try:
                invoice = Invoice.objects.create(
                    company=company,
                    billing=billing,
                    invoice_title=f"{company.company_name}_{billing_details['name']}",
                    invoice_type=bill_type,
                    invoice_product=products,
                    invoice_total=total_amount,
                    use_billing_address=shipping_details.get('use_billing_address', True),
                    shipping_address=shipping_details.get('address'),
                    shipping_pincode=shipping_details.get('pincode')
                )
            except Exception as e:
                logger.error(f"Error creating invoice: {str(e)}")
                return JsonResponse({'error': 'Error creating invoice record'}, status=400)

            # Generate PDF
            buffer = BytesIO()
            try:
                pdf = canvas.Canvas(buffer, pagesize=A4)
                styles = getSampleStyleSheet()  # Add this line to define styles
                
                # Add company logo if exists - positioned at the left edge with no border
                if company.company_logo and hasattr(company.company_logo, 'path'):
                    try:
                        pdf.saveState()
                        # Position logo at far left
                        pdf.drawImage(company.company_logo.path, 40, 780, width=60, height=40, preserveAspectRatio=True)
                        pdf.restoreState()
                    except Exception as e:
                        logger.warning(f"Could not add company logo: {str(e)}")
                        # Draw "LOGO" text as fallback - positioned at far left
                        pdf.setFont("Helvetica-Bold", 16)
                        pdf.drawString(40, 800, "LOGO")
                else:
                    # Draw "LOGO" text as fallback - positioned at far left
                    pdf.setFont("Helvetica-Bold", 16)
                    pdf.drawString(40, 800, "LOGO")

                # Invoice header with light blue color (as shown in the image)
                pdf.setFont("Helvetica-Bold", 24)
                pdf.setFillColor(colors.Color(0.4, 0.4, 0.8, alpha=0.3))
                header_text = "TAX INVOICE" if bill_type == "Invoice" else "PROFORMA INVOICE"
                # Position the header at right side (as in image)
                header_width = pdf.stringWidth(header_text, "Helvetica-Bold", 24)
                x_position = 550 - header_width  # Right align
                pdf.drawString(x_position, 800, header_text)
                
                # Invoice details - right aligned
                pdf.setFillColor(colors.black)
                pdf.setFont("Helvetica", 10)
                from datetime import datetime
                
                # Date and Invoice # right aligned (as in image)
                pdf.drawRightString(550, 780, f"Date: {datetime.now().strftime('%B %d, %Y')}")
                pdf.drawRightString(550, 765, f"Invoice #: {company.company_invoice_prefix}")
                
                # Added margin from top - moved the boxes down by 20 points
                # Left side company details with border
                pdf.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
                # pdf.rect(x, y, width, height, stroke, fill) draws a rectangle where:
                # x=40: Distance from left edge of page in points
                # y=640: Distance from bottom edge of page in points 
                # width=220: Width of rectangle in points
                # height=130: Height of rectangle in points
                # stroke=1: Draw the outline of the rectangle
                # fill=0: Don't fill the rectangle with color
                pdf.roundRect(40, 600, 220, 150, 8, stroke=1, fill=0)
                
                # Company name in bold at top left of box - also moved down
                pdf.setFont("Helvetica-Bold", 12)
                pdf.setFillColor(colors.black)
                pdf.drawString(50, 730, company.company_name)  # Y position changed from 750 to 730
                
                # Company Details in gray with labels - all moved down by 20 points
                pdf.setFont("Helvetica", 10)
                pdf.setFillColor(colors.gray)
                pdf.drawString(50, 710, f"GST:")  # 730 -> 710
                pdf.drawString(50, 690, f"Phone:")  # 710 -> 690
                pdf.drawString(50, 670, f"Email:")  # 690 -> 670
                pdf.drawString(50, 650, f"Address:")  # 670 -> 650
                pdf.drawString(50, 630, f"State:")  # 650 -> 630
                pdf.drawString(50, 610, f"Pincode:")  # Added pincode label
                
                # Company Details values in black - all moved down by 20 points
                pdf.setFillColor(colors.black)
                pdf.drawString(90, 710, company.company_gst_number)  # 730 -> 710
                pdf.drawString(90, 690, company.company_mobile_number)  # 710 -> 690
                pdf.drawString(90, 670, company.company_email)  # 690 -> 670
                
                # Handle multiline address - starting point moved down
                address_words = company.company_address.split()
                address_line = ""
                y_pos = 650  # 670 -> 650
                for word in address_words:
                    if pdf.stringWidth(address_line + " " + word, "Helvetica", 10) < 160:
                        address_line += " " + word
                    else:
                        pdf.drawString(90, y_pos, address_line.strip())
                        y_pos -= 15
                        address_line = word
                if address_line:
                    pdf.drawString(90, y_pos, address_line.strip())
                
                pdf.drawString(90, 630, company.company_state)  # 650 -> 630
                # Safely handle company_pincode which might be None
                pdf.drawString(90, 610, company.company_pincode or "")  # Added pincode value
                
                # Right side billing details with border - also moved down
                pdf.roundRect(270, 600, 280, 150, 8, stroke=1, fill=0)  # 640 -> 620
                
                # "Billed To:" header in blue - moved down
                pdf.setFont("Helvetica-Bold", 12)
                pdf.setFillColor(colors.Color(0.4, 0.4, 0.8))
                pdf.drawString(280, 730, "Billed To:")  # 750 -> 730
                
                # Billing company name in bold black - moved down
                pdf.setFillColor(colors.black)
                pdf.drawString(350, 730, billing_details['name'])  # 750 -> 730
                
                # Billing Details in gray with labels - all moved down
                pdf.setFillColor(colors.gray)
                pdf.setFont("Helvetica", 10)
                pdf.drawString(280, 710, f"GST:")  # 730 -> 710
                pdf.drawString(280, 690, f"Address:")  # 710 -> 690
                pdf.drawString(280, 670, f"Mobile:")  # 690 -> 670
                pdf.drawString(280, 650, f"Email:")  # 670 -> 650
                pdf.drawString(280, 630, f"State:")  # 650 -> 630
                
                # Billing Details values in black - all moved down
                pdf.setFillColor(colors.black)
                pdf.drawString(320, 710, billing_details['gstin'])  # 730 -> 710
                
                # Handle multiline address - starting point moved down
                address_words = billing_details['address'].split()
                address_line = ""
                y_pos = 690  # 710 -> 690
                for word in address_words:
                    if pdf.stringWidth(address_line + " " + word, "Helvetica", 10) < 220:
                        address_line += " " + word
                    else:
                        pdf.drawString(330, y_pos, address_line.strip())
                        y_pos -= 15
                        address_line = word
                if address_line:
                    pdf.drawString(330, y_pos, address_line.strip())
                
                pdf.drawString(330, 670, billing_details['mobile'])  # 690 -> 670
                pdf.drawString(330, 650, billing_details['email'])  # 670 -> 650
                pdf.drawString(330, 630, billing_details['state'])  # 650 -> 630
                pdf.drawString(280, 610, f"Pincode:")  # 630 -> 610
                # Get pincode safely with fallback to empty string
                pdf.drawString(330, 610, billing_details.get('pincode', ''))  # 630 -> 610
                
                # After getting company and billing details, add state comparison
                company_state = company.company_state
                billing_state = billing_details.get('state')
                is_same_state = company_state == billing_state

                # Reduce the gap by moving the table up closer to the header sections - start table at 560 instead of 500
                available_height = 560  
                
                # Table header with all data but modified display - exactly as in image
                table_data = [['Items Description', 'HSN', 'Unit Price', 'Unit', 'Qnt', 'Total']]
                
                # Rest of the code remains unchanged
                total_amount = Decimal('0.00')
                total_cgst = Decimal('0.00')
                total_sgst = Decimal('0.00')
                total_igst = Decimal('0.00')

                for product in products:
                    rate = Decimal(str(product['rate']))
                    quantity = Decimal(str(product['quantity']))
                    total = Decimal(str(product['total']))
                    unit_type = product.get('unit_type', '')
                    hsn = product.get('hsn', '')
                    gst_percentage = Decimal(str(product.get('gst_percentage', '0')))
                    
                    # Calculate GST based on state (keep calculations but don't show in table)
                    if is_same_state:
                        cgst_percentage = gst_percentage / 2
                        sgst_percentage = gst_percentage / 2
                        cgst_amount = (total * cgst_percentage) / Decimal('100')
                        sgst_amount = (total * sgst_percentage) / Decimal('100')
                        total_cgst += cgst_amount
                        total_sgst += sgst_amount
                    else:
                        igst_amount = (total * gst_percentage) / Decimal('100')
                        total_igst += igst_amount
                    
                    # Handle long HSN codes by wrapping if needed
                    if hsn and len(hsn) > 8:
                        hsn = Paragraph(hsn, styles['Normal'])
                    
                    # Table row with visible columns
                    description = [
                        Paragraph(f"<b>{product['name']}</b>", styles['Normal']),
                        hsn,
                        f"₹ {rate:,.2f}",
                        unit_type,
                        str(quantity),
                        f"₹ {total:,.2f}"
                    ]
                    
                    table_data.append(description)
                    total_amount += total

                # Set table column widths for visible columns and center align
                # Increase HSN column width to 80 (from 60) to better fit content
                table = Table(table_data, colWidths=[200, 80, 80, 50, 50, 60], repeatRows=1)
                page_width = A4[0]
                table_width = sum([200, 80, 80, 50, 50, 60])
                x_offset = (page_width - table_width) / 2

                # Enhanced table styling (keeping original style)
                table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.4, 0.4, 0.8)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),  # Center align numeric columns
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Left align description
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Reduced from 12
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.9, 0.9, 0.9)),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),  # Reduced from 15
                    ('TOPPADDING', (0, 1), (-1, -1), 8),     # Reduced from 15
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.Color(0.2, 0.2, 0.7)), # Strong header line
                    # Removed BOX style to eliminate the outer border
                ])
                table.setStyle(table_style)
                
                # Calculate the table height based on content - adjusted for tighter spacing
                row_height = 16 + 10  # 16 for padding (8 top + 8 bottom) + 10 for text height
                header_height = 8 + 11  # 8 for bottom padding + 11 for font size
                table_height = (len(table_data) - 1) * row_height + header_height

                # Calculate available space on page
                available_height = 560  # Starting vertical position for table (reduced gap between header and table)

                # Define column width for footer sections - needed for both single and multi-page layouts
                col_width = 160

                # Check if table will fit on current page
                # Create fixed size table area for better layout consistency
                fixed_table_area_height = 250  # Fixed height for table area
                max_rows_in_main_area = int((fixed_table_area_height - header_height) / row_height)

                if len(table_data) - 1 > max_rows_in_main_area:
                    # Too many rows for fixed area - use pagination
                    # Table is too large - we need to handle pagination
                    rows_per_page = max(1, max_rows_in_main_area)
                    
                    # For first page - only show rows that fit in fixed area
                    first_page_data = [table_data[0]] + table_data[1:rows_per_page+1]
                    first_page_table = Table(first_page_data, colWidths=[200, 80, 80, 50, 50, 60])
                    first_page_table.setStyle(table_style)
                    actual_table_height = min(fixed_table_area_height, header_height + (len(first_page_data) - 1) * row_height)
                    
                    # Draw first page table
                    first_page_table.wrapOn(pdf, 400, actual_table_height)
                    first_page_table.drawOn(pdf, x_offset, available_height - actual_table_height)
                    
                    # Calculate bottom of first table
                    table_bottom = available_height - actual_table_height
                    
                    # Add continuation message - using standard font instead of Helvetica-Italic
                    pdf.setFillColor(colors.black)
                    pdf.setFont("Helvetica", 9)
                    pdf.drawCentredString(page_width/2, table_bottom - 15, "Continued on next page...")
                    
                    # Process remaining rows on new pages
                    remaining_rows = table_data[rows_per_page+1:]
                    page_num = 1
                    
                    while remaining_rows:
                        # Start a new page
                        pdf.showPage()
                        page_num += 1
                        
                        # Add header to identify this is a continuation
                        pdf.setFont("Helvetica-Bold", 14)
                        pdf.setFillColor(colors.Color(0.4, 0.4, 0.8, alpha=0.3))
                        pdf.drawCentredString(page_width/2, 800, f"Invoice Continuation - Page {page_num}")
                        
                        # Calculate how many rows fit on this page
                        continuation_page_height = 700  # More space on continuation pages
                        rows_this_page = min(len(remaining_rows), int(continuation_page_height / row_height))
                        
                        # Create and draw table for this page
                        this_page_data = [table_data[0]] + remaining_rows[:rows_this_page]
                        this_page_table = Table(this_page_data, colWidths=[200, 80, 80, 50, 50, 60])
                        this_page_table.setStyle(table_style)
                        this_page_table_height = header_height + (len(this_page_data) - 1) * row_height
                        
                        # Position table with proper spacing
                        top_margin = 750
                        this_page_table.wrapOn(pdf, 400, this_page_table_height)
                        this_page_table.drawOn(pdf, x_offset, top_margin - this_page_table_height)
                        
                        # Update remaining rows
                        remaining_rows = remaining_rows[rows_this_page:]
                        
                        # If there are more rows, add continuation message - using standard font
                        if remaining_rows:
                            pdf.setFont("Helvetica", 9)  # Changed from Helvetica-Italic to Helvetica
                            pdf.setFillColor(colors.black)
                            bottom_pos = top_margin - this_page_table_height - 15
                            pdf.drawCentredString(page_width/2, bottom_pos, "Continued on next page...")
                    
                    # Start a new page for summary and footer
                    pdf.showPage()
                    
                    # Add final page header
                    pdf.setFont("Helvetica-Bold", 14)
                    pdf.setFillColor(colors.Color(0.4, 0.4, 0.8, alpha=0.3))
                    pdf.drawCentredString(page_width/2, 800, f"Invoice Summary - Page {page_num+1}")
                    
                    # Position summary at top of this page
                    summary_top = 700
                    note_top = 550
                    footer_top = 380
                else:
                    # Table fits in the fixed area - maintain table height within constraints
                    actual_table_height = header_height + (len(table_data) - 1) * row_height
                    
                    # Draw the table at the calculated position, but ensure it stays within fixed area
                    table.wrapOn(pdf, 400, actual_table_height)
                    table.drawOn(pdf, x_offset, available_height - actual_table_height)
                    
                    # Always position the summary section at consistent location
                    # This makes layout consistent regardless of number of rows
                    table_bottom = available_height - fixed_table_area_height
                    summary_top = table_bottom - 40  # Fixed position for summary
                    note_top = summary_top - 150     # Fixed position for notes
                    footer_top = note_top - 120      # Fixed position for footer

                # Create summary table for better alignment with product table
                summary_data = []
                summary_data.append(["Subtotal:", f"₹ {total_amount:,.2f}"])
                
                # Tax section based on state
                if is_same_state:
                    summary_data.append(["CGST:", f"₹ {total_cgst:,.2f}"])
                    summary_data.append(["SGST:", f"₹ {total_sgst:,.2f}"])
                    total_tax = total_cgst + total_sgst
                else:
                    summary_data.append(["IGST:", f"₹ {total_igst:,.2f}"])
                    total_tax = total_igst

                # Final total calculation
                final_total = total_amount + total_tax
                
                # Create aligned summary table
                summary_table = Table(summary_data, colWidths=[80, 115])
                summary_style = TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (1, -1), 8),
                    ('TOPPADDING', (0, 0), (1, -1), 8),
                    ('GRID', (0, 0), (1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
                ])
                summary_table.setStyle(summary_style)
                
                # Position summary table at right side to align with product table
                summary_x = x_offset + table_width - 195
                summary_table.wrapOn(pdf, 195, 75)
                summary_table.drawOn(pdf, summary_x, summary_top + 75)

                # Total due with shadow effect - adjust position to align with summary table
                pdf.saveState()
                pdf.setFillColor(colors.Color(0.4, 0.4, 0.8, alpha=0.3))
                pdf.roundRect(summary_x+2, summary_top+35, 195, 30, 5, fill=1)
                pdf.setFillColor(colors.Color(0.4, 0.4, 0.8))
                pdf.roundRect(summary_x, summary_top+33, 195, 30, 5, fill=1)
                pdf.setFillColor(colors.white)
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(summary_x+10, summary_top+45, "TOTAL DUE:")
                pdf.drawRightString(summary_x+185, summary_top+45, f"₹ {final_total:,.2f}")
                pdf.restoreState()
                
                # Note section with border - adjust position
                pdf.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
                pdf.rect(50, note_top, 500, 40, stroke=1)
                pdf.setFillColor(colors.gray)
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(60, note_top + 25, "Note:")
                pdf.setFont("Helvetica", 9)
                
                # Generate appropriate tax note based on state comparison
                if is_same_state:
                    # Ensure gst_percentage is defined and valid for the second instance
                    gst_percent_display = gst_percentage/2 if 'gst_percentage' in locals() else 0
                    tax_note = f"Note: GST is split equally as CGST ({gst_percent_display}%) and SGST ({gst_percent_display}%) as billing state matches company state."
                else:
                    gst_percent_display = gst_percentage if 'gst_percentage' in locals() else 0
                    tax_note = f"Note: Full GST ({gst_percent_display}%) is charged as IGST for inter-state transaction."
                
                pdf.drawString(60, note_top + 10, tax_note)
                
                # Footer with three columns and borders - adjust position
                pdf.rect(50, footer_top, col_width, 100, stroke=1)
                pdf.setFillColor(colors.black)
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(60, footer_top + 80, "Questions?")
                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(colors.gray)
                pdf.drawString(60, footer_top + 65, f"Email: {company.company_email}")
                pdf.drawString(60, footer_top + 50, f"Phone: {company.company_mobile_number}")
                
                # Payment Info with clickable Pay Now button - adjust position
                pdf.rect(220, footer_top, col_width, 100, stroke=1)
                pdf.setFillColor(colors.black)
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(230, footer_top + 80, "Payment Info:")
                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(colors.gray)
                pdf.drawString(230, footer_top + 65, f"Bank: {company.company_bank_name}")
                pdf.drawString(230, footer_top + 50, f"A/C: {company.company_bank_account_number}")
                pdf.drawString(230, footer_top + 35, f"IFSC: {company.company_bank_ifsc_code}")

                # Draw UPI Pay Now button - adjust position
                upi_button_y = footer_top + 5
                pdf.setFillColor(colors.Color(0.13, 0.59, 0.95))  # Blue color
                pdf.roundRect(230, upi_button_y, 100, 25, 8, fill=1)
                
                # UPI Button text - adjust position
                pdf.setFillColor(colors.white)
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(250, upi_button_y + 8, "UPI Pay")
                
                # Make UPI button clickable with redirect to UPI payment page
                upi_payment_url = f"http://{request.get_host()}/invoicing/upi-payment/{company.company_id}/?amount={final_total}"
                pdf.linkURL(
                    upi_payment_url,
                    (230, upi_button_y, 330, upi_button_y + 25),
                    relative=0
                )

                # Add shipping address to PDF if different from billing - adjust position
                if not shipping_details.get('use_billing_address', True):
                    # Ship To section (third column)
                    pdf.rect(390, footer_top, col_width, 100, stroke=1)
                    pdf.setFillColor(colors.black)
                    pdf.setFont("Helvetica-Bold", 10)
                    pdf.drawString(400, footer_top + 80, "Ship To:")
                    pdf.setFont("Helvetica", 9)
                    pdf.setFillColor(colors.gray)
                    # Safely access shipping address and pincode
                    pdf.drawString(400, footer_top + 65, shipping_details.get('address', ''))
                    pdf.drawString(400, footer_top + 50, f"Pincode: {shipping_details.get('pincode', '')}")
                
                # Thank you message with blue color - keep it at bottom of page
                pdf.setFont("Helvetica-Bold", 11)
                pdf.setFillColor(colors.Color(0.4, 0.4, 0.8))
                pdf.drawString(50, 40, "Thank you for your Business!")
                
                pdf.save()
                buffer.seek(0)
                
                # Save PDF to invoice
                invoice.invoice_pdf.save(
                    f"{invoice.invoice_title}.pdf",
                    ContentFile(buffer.getvalue()),
                    save=True
                )

                # Return PDF response
                response = FileResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_title}.pdf"'
                return response

            except Exception as e:
                logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
                return JsonResponse({'error': f'Error generating PDF: {str(e)}'}, status=500)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.headers.get('X-Generate-PDF'):
            return self.generate_pdf(request)
        
        logger.debug("Processing invoice creation request")
        try:
            # Validate required fields
            required_fields = ['company', 'billing_type', 'billing_name', 'billing_gst', 
                             'billing_mobile', 'billing_email', 'billing_address', 'billing_state']
            
            for field in required_fields:
                if not request.POST.get(field):
                    raise ValueError(f"{field} is required")

            # Get form data
            company_id = request.POST.get('company')
            billing_type = request.POST.get('billing_type')
            billing_name = request.POST.get('billing_name')
            billing_gst = request.POST.get('billing_gst')
            billing_mobile = request.POST.get('billing_mobile')
            billing_email = request.POST.get('billing_email')
            billing_address = request.POST.get('billing_address')
            billing_state = request.POST.get('billing_state')

            # Get company instance
            company = Company.objects.get(company_id=company_id)

            # Validate GST format
            gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            if not re.match(gst_pattern, billing_gst):
                raise ValueError("Invalid GST number format")

            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', billing_email):
                raise ValueError("Invalid email format")

            # Validate mobile number
            if not re.match(r'^[0-9]{10}$', billing_mobile):
                raise ValueError("Invalid mobile number format")

            # Create billing
            logger.debug("Creating billing record")
            billing = Billing.objects.create(
                # user=request.user,
                company=company,
                billing_name=billing_name,
                billing_gst_number=billing_gst,
                billing_phone=billing_mobile,
                billing_email=billing_email,
                billing_address=billing_address,
                billing_state=billing_state
            )

            # Calculate total amount and prepare products data
            total_amount = Decimal('0.00')
            products_data = json.loads(request.POST.get('products', '[]'))
            
            # Process products and calculate total
            processed_products = []
            for product_data in products_data:
                product_total = Decimal(str(product_data['total']))
                total_amount += product_total
                
                processed_products.append({
                    'name': product_data['name'],
                    'hsn': product_data['hsn'],
                    'quantity': int(product_data['quantity']),
                    'rate': str(product_data['rate']),
                    'total': str(product_total)
                })

            user_session_id = request.session.get('user_session_id')
            if not user_session_id:
                return JsonResponse({'success': False, 'message': 'User not authenticated'}, status=401)
            
            try:
                user_session = UserSession.objects.get(id=user_session_id)
                user = user_session.user
                user_id = user.user_id
            except UserSession.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid session'}, status=401)
            
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                print("User does not exist")
            # Create invoice with products JSON
            invoice = Invoice.objects.create(
                user=user,
                company=company,
                billing=billing,
                invoice_title=f"{company.company_name}_{billing_name}",
                invoice_type=billing_type,
                invoice_product=processed_products,
                invoice_total=total_amount,
                invoice_created_at=datetime.now(),
                invoice_updated_at=datetime.now()
            )

            return JsonResponse({
                'success': True,
                'message': 'Invoice created successfully',
                'redirect_url': '/invoicing/invoices/'
            })

        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            return JsonResponse({'error': 'Company not found'}, status=404)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

class UpiPaymentView(TemplateView):
    template_name = 'invoicing/upi_payment.html'

    def get_context_data(self, **kwargs):
        logger.debug("Entering get_context_data for UpiPaymentView")
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')  # Get from URL parameters
        amount = self.request.GET.get('amount')
        submitted = self.request.GET.get('submitted', 'false')
        
        logger.debug(f"Processing request with company_id: {company_id}, amount: {amount}, submitted: {submitted}")
        invoice_id = self.request.GET.get('invoice_id')
        logger.debug(f"Invoice ID: {invoice_id}")

        if not company_id:
            logger.warning("Company ID not provided in request")
            context['error'] = 'Company ID is required'
            return context
        
        try:
            company = Company.objects.get(company_id=company_id)
            logger.debug(f"Found company: {company.company_name}")
            
            # Format amount properly - ensure it's not None
            try:
                amount_decimal = Decimal(amount or '0.00')
                formatted_amount = f"{amount_decimal:.2f}"
                logger.debug(f"Formatted amount: {formatted_amount}")
            except (TypeError, ValueError):
                logger.warning(f"Invalid amount value: {amount}, using default 0.00")
                amount_decimal = Decimal('0.00')
                formatted_amount = '0.00'
            
            # Generate UPI links for different apps
            upi_id = company.company_upi_id
            company_name = quote(company.company_name)
            transaction_note = quote("Invoice Payment")
            
            logger.debug(f"Generating UPI links with UPI ID: {upi_id}")
            
            # Base UPI link
            base_upi_link = f"upi://pay?pa={upi_id}&pn={company_name}&am={formatted_amount}&cu=INR&tn={transaction_note}"
            
            # App-specific links
            phonepe_link = f"phonepe://{base_upi_link}"
            gpay_link = f"gpay://{base_upi_link}"
            paytm_link = f"paytmmp://{base_upi_link}"
            
            logger.debug("Generating QR code")
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(base_upi_link)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            qr_image_url = f"data:image/png;base64,{qr_image_base64}"
            
            logger.debug("QR code generated successfully")
            
            context.update({
                'company': company,
                'amount': formatted_amount,
                'phonepe_link': phonepe_link,
                'gpay_link': gpay_link,
                'paytm_link': paytm_link,
                'qr_image_url': qr_image_url,
                'submitted': submitted,
                'invoice_id': invoice_id
            })
            
        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            context['error'] = 'Company not found'
        except Exception as e:
            logger.error(f"Error processing UPI payment: {str(e)}", exc_info=True)
            context['error'] = str(e)
            
        logger.debug("Exiting get_context_data")
        return context

    def post(self, request, company_id, *args, **kwargs):
        logger.debug(f"Entering post method for company_id: {company_id}")
        try:
            # Get company using company_id from URL parameter
            company = Company.objects.get(company_id=company_id)
            invoice_id = request.POST.get('invoice_id')
            logger.debug(f"Processing post request for invoice_id: {invoice_id}")
            
            # Handle screenshot upload
            if 'payment_screenshot' in request.FILES:
                logger.debug("Payment screenshot found in request")
                screenshot = request.FILES['payment_screenshot']
                
                # Get amount with proper error handling
                amount_str = request.POST.get('amount', '0.00')
                try:
                    amount = Decimal(amount_str or '0.00')
                    logger.debug(f"Parsed amount: {amount}")
                except (TypeError, ValueError):
                    logger.warning(f"Invalid amount value: {amount_str}, using default 0.00")
                    amount = Decimal('0.00')
                
                # Find existing invoice with matching company and amount
                logger.debug("Searching for matching invoice")
                invoice = Invoice.objects.filter(
                    company=company,
                    invoice_id=invoice_id,
                    invoice_total=amount,
                    payment_screenshot__isnull=True
                ).order_by('-invoice_created_at').first()
                
                if invoice:
                    # Save screenshot to existing invoice
                    logger.debug(f"Found matching invoice {invoice.invoice_id}, saving screenshot")
                    invoice.payment_screenshot = screenshot
                    invoice.save()
                    logger.info(f"Payment screenshot added to invoice {invoice.invoice_id}")
                    
                    # Redirect to the same page with submitted parameter
                    redirect_url = f"/invoicing/upi-payment/{company_id}/?submitted=true"
                    return redirect(redirect_url)
                else:
                    logger.warning("No matching invoice found for screenshot upload")
                    return JsonResponse({'error': 'No matching invoice found'}, status=404)
            
            return self.get(request, company_id, *args, **kwargs)
            
        except Company.DoesNotExist:
            logger.error(f"Company with ID {company_id} not found")
            return JsonResponse({'error': 'Company not found'}, status=404)
        except Exception as e:
            logger.error(f"Error processing payment screenshot: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def render_to_response(self, context, **response_kwargs):
        logger.debug("Entering render_to_response")
        # If there's an error and it's an AJAX request, return JSON response
        if 'error' in context and self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.debug("Returning JSON error response for AJAX request")
            return JsonResponse({'error': context['error']}, status=400)
        logger.debug("Returning normal template response")
        return super().render_to_response(context, **response_kwargs)

class RecipientAuthView(TemplateView):
    template_name = 'invoicing/recipient_auth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        try:
            mobile = request.POST.get('mobile')
            security_code = request.POST.get('security_code') 
            passcode = request.POST.get('passcode')

            # Validate required fields
            if not all([mobile, security_code]):
                raise ValueError("Mobile number and security code are required")

            # Validate mobile number format
            if not mobile.isdigit() or len(mobile) != 10:
                raise ValueError("Invalid mobile number format")

            # Check if recipient exists with given mobile
            try:
                recipient = Recipent.objects.get(recipent_mobile_number=mobile)
                
                # Verify security code with check_password
                if not check_password(security_code, recipient.security_code):
                    raise ValueError("Invalid security code")

                # If passcode is provided, verify it
                if passcode:
                    if recipient.passcode != passcode:
                        raise ValueError("Invalid passcode")
                    
                    # Set session variables to maintain auth state
                    request.session['recipient_authenticated'] = True
                    request.session['recipient_id'] = str(recipient.recipent_id)
                    
                    # Get companies associated with recipient
                    companies = recipient.companies.all()
                    if companies.count() == 1:
                        # If there's only one company, redirect directly to that company's reports
                        logger.info(f"Recipient authenticated for single company: {mobile}")
                        company = companies.first()
                        return JsonResponse({
                            'success': True,
                            'redirect_url': f'/invoicing/reports/{company.company_id}/'
                        })
                    else:
                        # If multiple companies, redirect to company selection page
                        logger.info(f"Recipient authenticated for multiple companies: {mobile}")
                        return JsonResponse({
                            'success': True,
                            'redirect_url': '/invoicing/recipient/companies/'
                        })
                else:
                    # Return success without redirect to show passcode input
                    return JsonResponse({
                        'success': True,
                        'show_passcode': True
                    })

            except Recipent.DoesNotExist:
                raise ValueError("Mobile number not found")

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error authenticating recipient: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

class CreateRecipientView(View):
    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        try:
            # Get form data
            mobile_number = request.POST.get('mobile_number')
            security_code = request.POST.get('security_code')
            passcode = request.POST.get('passcode')
            selected_companies = request.POST.getlist('selected_companies[]')  # Get list of selected companies
            
            # Validate required fields
            if not all([mobile_number, security_code, passcode, selected_companies]):
                raise ValueError("All fields are required")
            
            # Validate mobile number format
            if not mobile_number.isdigit() or len(mobile_number) != 10:
                raise ValueError("Invalid mobile number format")
            user_session_id = request.session.get('user_session_id')
            if not user_session_id:
                return JsonResponse({'success': False, 'message': 'User not authenticated'}, status=401)
            
            try:
                user_session = UserSession.objects.get(id=user_session_id)
                user = user_session.user
                user_id = user.user_id
            except UserSession.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid session'}, status=401)
            
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                print("User does not exist")
            # Get company instances
            try:
                companies = [Company.objects.get(company_id=company_id) for company_id in selected_companies]
            except Company.DoesNotExist:
                raise ValueError("One or more selected companies not found")
                
            # Check if recipient with this mobile already exists
            existing_recipient = Recipent.objects.filter(recipent_mobile_number=mobile_number).first()
            if existing_recipient:
                # Update existing recipient
                existing_recipient.security_code = make_password(security_code)
                existing_recipient.passcode = passcode
                existing_recipient.companies.add(*companies)  # Add all selected companies
                existing_recipient.save()
                recipient = existing_recipient
                logger.info(f"Recipient updated: {mobile_number}")
            else:
                # Create new recipient with hashed security code
                recipient = Recipent.objects.create(
                    user=user,
                    recipent_mobile_number=mobile_number,
                    security_code=make_password(security_code),
                    passcode=passcode
                )
                # Add all selected companies to recipient's companies
                recipient.companies.add(*companies)
                logger.info(f"Recipient created: {mobile_number}")
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Recipient added successfully',
                'recipient_id': str(recipient.recipent_id)
            })
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating recipient: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

class ReportsView(TemplateView):
    template_name = 'invoicing/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        context['invoices'] = Invoice.objects.all()
        context['billings'] = Billing.objects.all()
        return context

    def mark_as_paid(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
        invoice.payment_status = True
        invoice.save()
        return redirect('/invoicing/reports/')
    
    def mark_as_unpaid(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
        invoice.payment_status = False
        invoice.save()
        return redirect('/invoicing/reports/')
    
STATE_CHOICES = [
    # States
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'), 
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    
    # Union Territories
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry')
]

class AddBillingView(TemplateView):
    template_name = 'invoicing/add_billing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        context['STATE_CHOICES'] = STATE_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        try:
            # Get form data
            company_id = request.POST.get('company')
            billing_name = request.POST.get('billing_name')
            billing_phone = request.POST.get('billing_phone')
            billing_email = request.POST.get('billing_email')
            billing_address = request.POST.get('billing_address')
            billing_state = request.POST.get('billing_state')

            # Validate required fields
            if not all([company_id, billing_name, billing_phone, billing_email, billing_address, billing_state]):
                raise ValueError("All fields are required")

            # Validate phone number format
            if not billing_phone.isdigit() or len(billing_phone) != 10:
                raise ValueError("Invalid phone number format")

            # Get company instance
            try:
                company = Company.objects.get(company_id=company_id)
            except Company.DoesNotExist:
                raise ValueError("Selected company not found")
            user_session_id = request.session.get('user_session_id')
            if not user_session_id:
                return JsonResponse({'success': False, 'message': 'User not authenticated'}, status=401)
            
            try:
                user_session = UserSession.objects.get(id=user_session_id)
                user = user_session.user
                user_id = user.user_id
            except UserSession.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid session'}, status=401)
            
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                print("User does not exist")
            # Create billing
            billing = Billing.objects.create(
                user=user,
                company=company,
                billing_name=billing_name,
                billing_phone=billing_phone,
                billing_email=billing_email,
                billing_address=billing_address,
                billing_state=billing_state
            )

            logger.info(f"Billing '{billing_name}' created successfully")
            return JsonResponse({
                'success': True,
                'message': 'Billing details added successfully',
                'redirect_url': '/invoicing/companies/'
            })

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating billing: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

