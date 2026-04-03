"""
PDF Report generation service for portfolio.
"""

import io
from datetime import datetime
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER


def generate_portfolio_pdf(
    holdings: List[dict],
    summary: dict,
    signals_data: Optional[dict] = None,
) -> bytes:
    """
    Generate a PDF report for the portfolio.
    
    Args:
        holdings: List of holding dictionaries
        summary: Portfolio summary dictionary
        signals_data: Optional signals data from portfolio/signals endpoint
    
    Returns:
        PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RightAlign',
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name='CenterAlign',
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
    ))
    
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor('#1f2937'),
    )
    elements.append(Paragraph("Portfolio Report", title_style))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    elements.append(Paragraph(f"Generated: {date_str}", styles['CenterAlign']))
    elements.append(Spacer(1, 20))
    
    # Summary Section
    summary_title = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor('#374151'),
    )
    elements.append(Paragraph("Portfolio Summary", summary_title))
    
    total_value = summary.get('total_current_value', 0) or 0
    total_cost = summary.get('total_cost', 0) or 0
    total_gain_loss = summary.get('total_gain_loss', 0) or 0
    total_gain_loss_pct = summary.get('total_gain_loss_pct', 0) or 0
    
    gain_loss_color = colors.green if total_gain_loss >= 0 else colors.red
    
    summary_data = [
        ["Total Market Value", f"${total_value:,.2f}"],
        ["Total Cost Basis", f"${total_cost:,.2f}"],
        ["Total Gain/Loss", f"${total_gain_loss:,.2f}"],
        ["Return", f"{total_gain_loss_pct:.2f}%"],
        ["Number of Holdings", str(len(holdings))],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (1, 2), (1, 2), gain_loss_color),
        ('TEXTCOLOR', (1, 3), (1, 3), gain_loss_color),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Holdings Section
    elements.append(Paragraph("Holdings", summary_title))
    
    if holdings:
        holdings_header = ["Symbol", "Type", "Shares", "Avg Cost", "Current Price", "Value", "Gain/Loss"]
        holdings_data = [holdings_header]
        
        for h in holdings:
            gain_loss = h.get('gain_loss', 0) or 0
            gain_loss_pct = h.get('gain_loss_pct', 0) or 0
            current_price = h.get('current_price') or 0
            current_value = h.get('current_value') or 0
            
            row = [
                h.get('symbol', ''),
                h.get('asset_type', 'STOCK'),
                f"{h.get('quantity', 0):.2f}",
                f"${h.get('avg_cost', 0):.2f}",
                f"${current_price:.2f}",
                f"${current_value:,.2f}",
                f"${gain_loss:,.2f} ({gain_loss_pct:.1f}%)",
            ]
            holdings_data.append(row)
        
        holdings_table = Table(
            holdings_data,
            colWidths=[0.8*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.9*inch, 0.9*inch, 1.2*inch]
        )
        
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]
        
        # Color gain/loss column
        for i, h in enumerate(holdings, 1):
            gain_loss = h.get('gain_loss', 0) or 0
            if gain_loss >= 0:
                table_style.append(('TEXTCOLOR', (6, i), (6, i), colors.HexColor('#059669')))
            else:
                table_style.append(('TEXTCOLOR', (6, i), (6, i), colors.HexColor('#dc2626')))
        
        holdings_table.setStyle(TableStyle(table_style))
        elements.append(holdings_table)
    else:
        elements.append(Paragraph("No holdings to display.", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # AI Signals Section (if available)
    if signals_data and signals_data.get('holdings'):
        elements.append(Paragraph("AI Signals Summary", summary_title))
        
        signals_header = ["Symbol", "Signal", "Confidence", "Summary"]
        signals_table_data = [signals_header]
        
        for item in signals_data['holdings'][:10]:  # Top 10
            h = item.get('holding', {})
            s = item.get('signal', {})
            signals_table_data.append([
                h.get('symbol', ''),
                s.get('signal_label', s.get('signal', '')),
                f"{s.get('confidence', 0):.0f}%",
                s.get('summary', '')[:60] + '...' if s.get('summary') else '',
            ])
        
        signals_table = Table(
            signals_table_data,
            colWidths=[0.8*inch, 1*inch, 0.8*inch, 4*inch]
        )
        
        signal_colors = {
            'STRONG_BUY': colors.HexColor('#059669'),
            'BUY': colors.HexColor('#10b981'),
            'HOLD': colors.HexColor('#d97706'),
            'SELL': colors.HexColor('#ea580c'),
            'STRONG_SELL': colors.HexColor('#dc2626'),
        }
        
        signal_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]
        
        for i, item in enumerate(signals_data['holdings'][:10], 1):
            sig = item.get('signal', {}).get('signal', '')
            if sig in signal_colors:
                signal_style.append(('TEXTCOLOR', (1, i), (1, i), signal_colors[sig]))
        
        signals_table.setStyle(TableStyle(signal_style))
        elements.append(signals_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        "This report is for informational purposes only and does not constitute financial advice.",
        footer_style
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
