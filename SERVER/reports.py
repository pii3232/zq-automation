from flask import Blueprint, request, jsonify, send_file
from models import db, User, Order, ActivationCode, Activation, Ticket
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

# 尝试注册中文字体
def register_chinese_font():
    """注册中文字体"""
    try:
        # Windows字体路径
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
            '/System/Library/Fonts/PingFang.ttc',  # macOS
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return True
        return False
    except Exception as e:
        logger.warning(f"注册中文字体失败: {str(e)}")
        return False

# 注册字体
has_chinese_font = register_chinese_font()

# 生成报告的通用样式
def get_styles():
    """获取报告样式"""
    styles = getSampleStyleSheet()

    if has_chinese_font:
        # 创建支持中文的样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Heading1'],
            fontName='ChineseFont',
            fontSize=24,
            spaceAfter=30
        ))
        styles.add(ParagraphStyle(
            name='ChineseHeading',
            parent=styles['Heading2'],
            fontName='ChineseFont',
            fontSize=16,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName='ChineseFont',
            fontSize=10
        ))
        return styles
    else:
        # 英文样式
        styles['Title'].fontSize = 24
        styles['Heading2'].fontSize = 16
        return styles


def create_pdf_report(title, sections, filename):
    """创建PDF报告"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    story = []
    styles = get_styles()

    # 标题
    if has_chinese_font:
        story.append(Paragraph(title, styles['ChineseTitle']))
    else:
        story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 12))

    # 生成时间
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if has_chinese_font:
        story.append(Paragraph(f"生成时间: {gen_time}", styles['ChineseNormal']))
    else:
        story.append(Paragraph(f"Generated: {gen_time}", styles['Normal']))
    story.append(Spacer(1, 24))

    # 各个部分
    for section in sections:
        # 小节标题
        if has_chinese_font:
            story.append(Paragraph(section['title'], styles['ChineseHeading']))
        else:
            story.append(Paragraph(section['title'], styles['Heading2']))
        story.append(Spacer(1, 6))

        # 表格数据
        if 'data' in section and section['data']:
            data = section['data']
            headers = section.get('headers', [])
            
            # 如果有标题行，添加到数据中
            if headers:
                table_data = [headers] + data
            else:
                table_data = data

            # 创建表格
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont' if has_chinese_font else 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont' if has_chinese_font else 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(table)
            story.append(Spacer(1, 24))
        elif 'text' in section:
            # 文本内容
            if has_chinese_font:
                story.append(Paragraph(section['text'], styles['ChineseNormal']))
            else:
                story.append(Paragraph(section['text'], styles['Normal']))
            story.append(Spacer(1, 24))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ==================== 报表API ====================

@reports_bp.route('/report/users', methods=['GET'])
def generate_user_report():
    """生成用户注册报告"""
    try:
        users = User.query.all()

        # 准备表格数据
        headers = ['ID', '用户名', '邮箱', '注册时间', '状态']
        data = []
        for user in users:
            status = '活跃' if user.is_active else '禁用'
            data.append([
                str(user.id),
                user.username,
                user.email,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                status
            ])

        # 统计信息
        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active)
        inactive_users = total_users - active_users

        summary_text = f"""
        <b>用户统计:</b>
        总用户数: {total_users}
        活跃用户: {active_users}
        禁用用户: {inactive_users}
        """

        sections = [
            {
                'title': '用户统计摘要',
                'text': summary_text
            },
            {
                'title': '用户列表',
                'headers': headers,
                'data': data
            }
        ]

        # 生成PDF
        buffer = create_pdf_report('用户注册报告', sections, 'user_report.pdf')
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'用户注册报告_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"生成用户报告失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@reports_bp.route('/report/orders', methods=['GET'])
def generate_order_report():
    """生成支付报告"""
    try:
        orders = Order.query.all()

        # 准备表格数据
        headers = ['订单号', '用户', '金额(元)', '数量', '单价', '状态', '创建时间', '支付时间']
        data = []
        total_amount = 0
        paid_orders = 0

        for order in orders:
            username = order.user.username if order.user else 'N/A'
            status_map = {
                'pending': '待支付',
                'paid': '已支付',
                'failed': '失败'
            }
            status = status_map.get(order.status, order.status)

            data.append([
                order.order_no,
                username,
                f"{order.amount:.2f}",
                str(order.quantity),
                f"{order.unit_price:.2f}",
                status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
                order.paid_at.strftime('%Y-%m-%d %H:%M:%S') if order.paid_at else ''
            ])

            total_amount += order.amount if order.status == 'paid' else 0
            if order.status == 'paid':
                paid_orders += 1

        # 统计信息
        summary_text = f"""
        <b>订单统计:</b>
        总订单数: {len(orders)}
        已支付订单: {paid_orders}
        待支付订单: {len(orders) - paid_orders}
        总支付金额: ¥{total_amount:.2f}
        """

        sections = [
            {
                'title': '订单统计摘要',
                'text': summary_text
            },
            {
                'title': '订单列表',
                'headers': headers,
                'data': data
            }
        ]

        # 生成PDF
        buffer = create_pdf_report('支付报告', sections, 'order_report.pdf')
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'支付报告_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"生成支付报告失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@reports_bp.route('/report/codes', methods=['GET'])
def generate_code_report():
    """生成激活码统计报告"""
    try:
        codes = ActivationCode.query.all()

        # 准备表格数据
        headers = ['ID', '激活码', '使用用户名', '邀请码', '订单号', '状态', '创建时间']
        data = []
        unused_count = 0
        used_count = 0
        expired_count = 0

        for code in codes:
            # 获取激活记录中的用户名和邀请码
            user_name = 'N/A'
            invite_code_used = 'N/A'

            # 查找使用该激活码的激活记录
            activation = Activation.query.filter_by(code_id=code.id).first()
            if activation:
                user_name = activation.user.username if activation.user else 'N/A'
                invite_code_used = activation.invite_code if activation.invite_code else 'N/A'

            order_no = code.order.order_no if code.order else 'N/A'
            status_map = {
                'unused': '未使用',
                'used': '已使用',
                'expired': '已过期'
            }
            status = status_map.get(code.status, code.status)

            data.append([
                str(code.id),
                code.code[:10] + '...',  # 只显示前10位
                user_name,
                invite_code_used,
                order_no,
                status,
                code.created_at.strftime('%Y-%m-%d %H:%M:%S') if code.created_at else ''
            ])

            if code.status == 'unused':
                unused_count += 1
            elif code.status == 'used':
                used_count += 1
            else:
                expired_count += 1

        # 统计信息
        summary_text = f"""
        <b>激活码统计:</b>
        总激活码数: {len(codes)}
        未使用: {unused_count}
        已使用: {used_count}
        已过期: {expired_count}
        """

        sections = [
            {
                'title': '激活码统计摘要',
                'text': summary_text
            },
            {
                'title': '激活码列表',
                'headers': headers,
                'data': data
            }
        ]

        # 生成PDF
        buffer = create_pdf_report('激活码统计报告', sections, 'code_report.pdf')
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'激活码统计报告_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"生成激活码报告失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@reports_bp.route('/report/tickets', methods=['GET'])
def generate_ticket_report():
    """生成报障表报告"""
    try:
        tickets = Ticket.query.all()

        # 准备表格数据
        headers = ['工单号', '用户', '标题', '联系人', '电话', '状态', '创建时间', '更新时间']
        data = []
        status_count = {'pending': 0, 'processing': 0, 'resolved': 0, 'closed': 0}

        for ticket in tickets:
            username = ticket.user.username if ticket.user else 'N/A'
            status_map = {
                'pending': '待处理',
                'processing': '处理中',
                'resolved': '已解决',
                'closed': '已关闭'
            }
            status = status_map.get(ticket.status, ticket.status)
            status_count[ticket.status] = status_count.get(ticket.status, 0) + 1

            data.append([
                str(ticket.id),
                username,
                ticket.title[:30] + '...' if len(ticket.title) > 30 else ticket.title,
                ticket.contact_person,
                ticket.contact_phone,
                status,
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else '',
                ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else ''
            ])

        # 统计信息
        summary_text = f"""
        <b>报障工单统计:</b>
        总工单数: {len(tickets)}
        待处理: {status_count.get('pending', 0)}
        处理中: {status_count.get('processing', 0)}
        已解决: {status_count.get('resolved', 0)}
        已关闭: {status_count.get('closed', 0)}
        """

        sections = [
            {
                'title': '报障工单统计摘要',
                'text': summary_text
            },
            {
                'title': '报障工单列表',
                'headers': headers,
                'data': data
            }
        ]

        # 生成PDF
        buffer = create_pdf_report('报障表报告', sections, 'ticket_report.pdf')
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'报障表报告_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"生成报障报告失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@reports_bp.route('/report/all', methods=['GET'])
def generate_all_reports():
    """一键生成所有报告"""
    try:
        from flask import send_file
        import zipfile
        from io import BytesIO

        # 创建ZIP文件
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 生成用户报告
            users = User.query.all()
            headers = ['ID', '用户名', '邮箱', '注册时间', '状态']
            data = [[str(u.id), u.username, u.email,
                    u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else '',
                    '活跃' if u.is_active else '禁用'] for u in users]
            buffer = create_pdf_report('用户注册报告',
                [{'title': '用户列表', 'headers': headers, 'data': data}],
                'user_report.pdf')
            zipf.writestr('用户注册报告.pdf', buffer.getvalue())

            # 生成支付报告
            orders = Order.query.all()
            headers = ['订单号', '用户', '金额', '数量', '状态', '创建时间']
            data = [[o.order_no, o.user.username if o.user else 'N/A',
                    f"{o.amount:.2f}", str(o.quantity), o.status,
                    o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else '']
                    for o in orders]
            buffer = create_pdf_report('支付报告',
                [{'title': '订单列表', 'headers': headers, 'data': data}],
                'order_report.pdf')
            zipf.writestr('支付报告.pdf', buffer.getvalue())

            # 生成激活码报告
            codes = ActivationCode.query.all()
            headers = ['ID', '激活码', '订单号', '状态', '创建时间']
            data = [[str(c.id), c.code[:10] + '...', c.order.order_no if c.order else 'N/A',
                    c.status, c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else '']
                    for c in codes]
            buffer = create_pdf_report('激活码统计报告',
                [{'title': '激活码列表', 'headers': headers, 'data': data}],
                'code_report.pdf')
            zipf.writestr('激活码统计报告.pdf', buffer.getvalue())

            # 生成报障报告
            tickets = Ticket.query.all()
            headers = ['工单号', '用户', '标题', '状态', '创建时间']
            data = [[str(t.id), t.user.username if t.user else 'N/A',
                    t.title[:20] + '...' if len(t.title) > 20 else t.title,
                    t.status, t.created_at.strftime('%Y-%m-%d %H:%M:%S') if t.created_at else '']
                    for t in tickets]
            buffer = create_pdf_report('报障表报告',
                [{'title': '报障工单列表', 'headers': headers, 'data': data}],
                'ticket_report.pdf')
            zipf.writestr('报障表报告.pdf', buffer.getvalue())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'所有报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"一键生成报告失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
