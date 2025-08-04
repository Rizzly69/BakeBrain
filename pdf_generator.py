from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
from datetime import datetime
import io
import os
from models import Order, OrderItem, User, Product

class SmartBillGenerator:
    """Advanced PDF bill generation with professional formatting"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Create custom styles for professional invoices"""
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=10,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica-Bold',
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='DetailText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=4
        ))
    
    def generate_invoice_pdf(self, order_id):
        """Generate a professional invoice PDF"""
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build the invoice content
        story = []
        
        # Header with company info
        story.append(Paragraph("Smart Bakery Manager", self.styles['CompanyHeader']))
        story.append(Paragraph("Premium Artisan Bakery", self.styles['DetailText']))
        story.append(Paragraph("123 Baker Street, Bakery District", self.styles['DetailText']))
        story.append(Paragraph("Phone: (555) 123-BAKE | Email: orders@smartbakery.com", self.styles['DetailText']))
        story.append(Spacer(1, 20))
        
        # Invoice header
        story.append(Paragraph(f"INVOICE #{order.order_number}", self.styles['InvoiceTitle']))
        
        # Invoice details table
        invoice_details = [
            ['Invoice Date:', order.created_at.strftime('%B %d, %Y')],
            ['Order Type:', order.order_type.value.title()],
            ['Status:', order.status.value.replace('_', ' ').title()],
            ['Customer:', f"{order.customer.first_name} {order.customer.last_name}"]
        ]
        
        if order.delivery_date:
            invoice_details.append(['Delivery Date:', order.delivery_date.strftime('%B %d, %Y')])
        
        if order.delivery_address:
            invoice_details.append(['Delivery Address:', order.delivery_address])
        
        details_table = Table(invoice_details, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 30))
        
        # Items table
        story.append(Paragraph("Order Items", self.styles['SectionHeader']))
        
        # Prepare items data
        items_data = [['Description', 'Qty', 'Unit Price', 'Total']]
        
        for item in order.items:
            items_data.append([
                item.product.name,
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.total_price:.2f}"
            ])
        
        # Add special instructions if any
        for item in order.items:
            if item.special_instructions:
                items_data.append([
                    f"  → {item.special_instructions}",
                    '', '', ''
                ])
        
        # Create items table
        items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Content styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            
            # Alignment
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#d1d5db')),
            
            # Padding
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Calculations
        subtotal = order.total_amount - order.tax_amount + order.discount_amount
        
        # Summary table
        summary_data = [
            ['Subtotal:', f"${subtotal:.2f}"],
        ]
        
        if order.discount_amount > 0:
            summary_data.append(['Discount:', f"-${order.discount_amount:.2f}"])
        
        summary_data.extend([
            ['Tax:', f"${order.tax_amount:.2f}"],
            ['', ''],  # Spacer row
            ['TOTAL:', f"${order.total_amount:.2f}"]
        ])
        
        summary_table = Table(summary_data, colWidths=[4*inch, 1.2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#3b82f6')),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Special notes for catering orders
        if order.order_type.value == 'catering':
            story.append(Paragraph("Event Details", self.styles['SectionHeader']))
            if order.event_date:
                story.append(Paragraph(f"Event Date: {order.event_date.strftime('%B %d, %Y at %I:%M %p')}", self.styles['DetailText']))
            if order.guest_count:
                story.append(Paragraph(f"Guest Count: {order.guest_count}", self.styles['DetailText']))
            if order.setup_requirements:
                story.append(Paragraph(f"Setup Requirements: {order.setup_requirements}", self.styles['DetailText']))
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 20))
        story.append(Paragraph("Thank you for choosing Smart Bakery Manager!", self.styles['DetailText']))
        story.append(Paragraph("Questions? Contact us at support@smartbakery.com", self.styles['DetailText']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_daily_sales_report(self, date):
        """Generate daily sales report PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        # Header
        story.append(Paragraph("Smart Bakery Manager", self.styles['CompanyHeader']))
        story.append(Paragraph(f"Daily Sales Report - {date.strftime('%B %d, %Y')}", self.styles['InvoiceTitle']))
        story.append(Spacer(1, 20))
        
        # Get orders for the day
        orders = Order.query.filter(
            Order.created_at >= date,
            Order.created_at < date.replace(hour=23, minute=59, second=59)
        ).all()
        
        if not orders:
            story.append(Paragraph("No orders found for this date.", self.styles['Normal']))
        else:
            # Summary statistics
            total_revenue = sum(order.total_amount for order in orders)
            total_orders = len(orders)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            summary_data = [
                ['Total Orders:', str(total_orders)],
                ['Total Revenue:', f"${total_revenue:.2f}"],
                ['Average Order Value:', f"${avg_order_value:.2f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Orders breakdown
            story.append(Paragraph("Orders Breakdown", self.styles['SectionHeader']))
            
            orders_data = [['Order #', 'Customer', 'Type', 'Amount', 'Status']]
            
            for order in orders:
                orders_data.append([
                    order.order_number,
                    f"{order.customer.first_name} {order.customer.last_name}",
                    order.order_type.value.title(),
                    f"${order.total_amount:.2f}",
                    order.status.value.replace('_', ' ').title()
                ])
            
            orders_table = Table(orders_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1*inch, 1.3*inch])
            orders_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ]))
            
            story.append(orders_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_inventory_report(self):
        """Generate comprehensive inventory report"""
        from models import Inventory, Product
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        # Header
        story.append(Paragraph("Smart Bakery Manager", self.styles['CompanyHeader']))
        story.append(Paragraph(f"Inventory Report - {datetime.now().strftime('%B %d, %Y')}", self.styles['InvoiceTitle']))
        story.append(Spacer(1, 20))
        
        # Get inventory data
        inventory_items = Inventory.query.join(Product).all()
        
        if not inventory_items:
            story.append(Paragraph("No inventory data available.", self.styles['Normal']))
        else:
            # Calculate totals
            total_items = len(inventory_items)
            low_stock_items = len([item for item in inventory_items if item.is_low_stock()])
            total_value = sum(item.quantity * float(item.product.cost or 0) for item in inventory_items)
            
            # Summary
            summary_data = [
                ['Total Products:', str(total_items)],
                ['Low Stock Items:', str(low_stock_items)],
                ['Total Inventory Value:', f"${total_value:.2f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Detailed inventory
            story.append(Paragraph("Detailed Inventory", self.styles['SectionHeader']))
            
            inventory_data = [['Product', 'Current Stock', 'Min Level', 'Max Level', 'Status', 'Value']]
            
            for item in inventory_items:
                status = "LOW STOCK" if item.is_low_stock() else "OK"
                value = item.quantity * float(item.product.cost or 0)
                
                inventory_data.append([
                    item.product.name,
                    str(item.quantity),
                    str(item.min_stock_level),
                    str(item.max_stock_level),
                    status,
                    f"${value:.2f}"
                ])
            
            inventory_table = Table(inventory_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
            inventory_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ]))
            
            story.append(inventory_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer