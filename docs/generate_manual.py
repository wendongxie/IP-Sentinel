"""Generate the Chinese Word manual from its editable chapter source."""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

root = Path(__file__).resolve().parent
title = "IP Sentinel 用户使用手册"
output = root / "IP_Sentinel_V1.2.0_用户使用手册.docx"
lines = (root / "manual_zh.txt").read_text(encoding="utf-8-sig").splitlines()
document = Document()
document.core_properties.title = title
document.core_properties.author = "文东工作室"
document.core_properties.subject = "V1.2.0 Windows 安装、检测及通知配置"
section = document.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.left_margin = section.right_margin = Inches(0.92)
section.top_margin = section.bottom_margin = Inches(0.8)
section.different_first_page_header_footer = True
section.header.paragraphs[0].text = "IP Sentinel V1.2.0  用户使用手册"


def typography(style, size, font="Microsoft YaHei"):
    style.font.name = font
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


for style_name, size in (("Normal", 11), ("Title", 32), ("Heading 1", 19),
                         ("Heading 2", 13), ("Caption", 9), ("Header", 9),
                         ("Footer", 9), ("List Number", 11)):
    typography(document.styles[style_name], size)
for name in ("Normal", "List Number"):
    style = document.styles[name]
    style.paragraph_format.space_after = Pt(7)
    style.paragraph_format.line_spacing = 1.22
title_style = document.styles["Title"]
title_style.paragraph_format.space_after = Pt(24)
style_properties = title_style.element.get_or_add_pPr()
for border in style_properties.findall(qn("w:pBdr")):
    style_properties.remove(border)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run("文东工作室  ·  ")
number = OxmlElement("w:fldSimple")
number.set(qn("w:instr"), "PAGE")
footer._p.append(number)

cover = document.add_paragraph(style="Title")
cover.paragraph_format.space_before = Pt(110)
cover.add_run(title)
document.add_paragraph("V1.2.0  |  Windows x64").runs[0].font.size = Pt(17)
logo = root.parent / "assets" / "icons" / "ip-sentinel.png"
document.add_picture(str(logo), width=Inches(1.6))
document.add_paragraph("安装、检测、风险结果与通知配置")
document.add_paragraph("文东工作室出品")
document.add_page_break()
quick = document.add_paragraph()
quick_run = quick.add_run("快速上手")
quick_run.bold = True
quick_run.font.size = Pt(19)
for step in (
    "1. 安装后从桌面打开；使用便携版时先完整解压 ZIP，再运行 IP Sentinel.exe。",
    "2. 打开“当前出口”，点击“立即检测”。首次启动后可稍等名单下载，再检查风险结果。",
    "3. 需要告警时，在“凭据与通知设置”配置接收渠道。首次成功检测只建立地址基线。",
):
    document.add_paragraph(step)
p = document.add_paragraph()
p.add_run("费用提示 ").bold = True
p.add_run("免费公开名单无需密钥。IPWhois Pro API 是可选收费服务；需要接口风险字段时，请查看第五章的套餐对照。")
toc_title = document.add_paragraph("目录")
toc_title.runs[0].bold = True
toc_title.runs[0].font.size = Pt(23)
document.add_paragraph("在 Word 中右键目录并选择“更新域”，即可刷新页码和章节。")


def field_part(paragraph, kind):
    marker = OxmlElement("w:fldChar")
    marker.set(qn("w:fldCharType"), kind)
    paragraph.add_run()._r.append(marker)


toc = document.add_paragraph()
field_part(toc, "begin")
instruction = OxmlElement("w:instrText")
instruction.set(qn("xml:space"), "preserve")
instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
toc.add_run()._r.append(instruction)
field_part(toc, "separate")
chapters = [line[2:] for line in lines if line.startswith("# ")]
for index, chapter in enumerate(chapters, 1):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.line_spacing = 1.08
    link = OxmlElement("w:hyperlink")
    link.set(qn("w:anchor"), f"chapter_{index}")
    run = paragraph.add_run(chapter)
    run.font.color.rgb = RGBColor.from_string("21496F")
    link.append(run._r)
    paragraph._p.append(link)
field_part(document.paragraphs[-1], "end")
document.add_page_break()
update = OxmlElement("w:updateFields")
update.set(qn("w:val"), "true")
document.settings.element.append(update)


def image_and_caption(line):
    image, caption = line[3:-1].split("|", 1)
    file = root / "screenshots" / f"{image}.png"
    if file.is_file():
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.keep_with_next = True
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        width = 5.1 if image in {"overview", "history"} else 4.35
        paragraph.add_run().add_picture(str(file), width=Inches(width))
        document.add_paragraph(caption, "Caption").alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        document.add_paragraph(f"截图待补充  {caption}", "Caption")


TABLE_ROWS = {
    "安装": (
        ("使用方式", "安装与数据"),
        ("安装版", "运行安装包，可创建桌面快捷方式，并可在开始菜单打开手册。通过 Windows 设置卸载。"),
        ("便携版", "完整解压 ZIP，运行 IP Sentinel.exe。程序依赖位于旁边的 _internal 文件夹。无需安装 Python。"),
    ),
    "标签": (
        ("界面状态", "含义"),
        ("名单命中", "当前地址出现在该公开名单中。"),
        ("该名单未收录", "本次名单未找到该地址，不能由此判断是否安全或属于住宅宽带。"),
        ("命中 / 未标记", "接口提供的布尔标签。判断范围限于这次查询和该数据源。"),
        ("未知", "可能尚未取得缓存、该名单不覆盖当前协议，或接口缺少风险字段。"),
    ),
    "费用": (
        ("服务", "月付价格与用途"),
        ("免费归属接口", "0 美元。查询基本归属信息，不提供接口安全标签。"),
        ("Basic", "19.99 美元/月。付费套餐，不包含 Security Data。"),
        ("Business", "39.99 美元/月。含 Security Data，是官网列出包含该项的最低月付套餐。"),
        ("Unlimited", "99.99 美元/月。继承 Business 的 Security Data。"),
    ),
    "故障": (
        ("现象", "先检查什么"),
        ("IPv6 未观测到", "检查本机网络是否具备 IPv6 和对应探测端点是否可达。IPv4 可独立成功。"),
        ("风险显示未知", "首次启动后稍后再检测。检查名单是否有版本或获取时间、是否覆盖该协议。已填 Pro 密钥时确认套餐含安全数据。"),
        ("浏览器 IP 不同", "对照程序显示的探测端点、同一协议和相近时间。代理或分流规则可能让浏览器和程序使用不同出口。"),
        ("切换后无告警", "在“历史与统计”确认该协议已有成功基线，且出现了不同的新地址与“原 IP”。"),
        ("历史没有更新", "从托盘确认程序仍在运行，检查电脑是否休眠，点击“立即检测”观察状态栏。"),
        ("远程告警未送达", "先查看本次状态栏。Telegram 检查会话 ID、Token 和群权限；企业微信检查 Webhook、群权限与频率限制。"),
        ("便携版探测失败", "确认已完整解压，并从解压文件夹启动。检查 _internal 是否和 EXE 位于同一目录。"),
    ),
}


def manual_table(rows):
    table = document.add_table(rows=0, cols=2)
    table.autofit = False
    widths = (1.65, 5.01)
    for column, width in zip(table.columns, widths):
        column.width = Inches(width)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{edge}")
        for prop, val in (("val", "single"), ("sz", "6"), ("color", "D9D9D9")):
            border.set(qn(f"w:{prop}"), val)
        borders.append(border)
    table._tbl.tblPr.append(borders)
    for index, values in enumerate(rows):
        row = table.add_row()
        if index == 0:
            row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.add_run(value).bold = index == 0
            p.paragraph_format.keep_with_next = index == 0
            if index == 0:
                fill = OxmlElement("w:shd")
                fill.set(qn("w:fill"), "E8F0F9")
                cell._tc.get_or_add_tcPr().append(fill)


def linked_url(url):
    paragraph = document.add_paragraph()
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True))
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "18")
    properties.append(size)
    run.append(properties)
    value = OxmlElement("w:t")
    value.text = url
    run.append(value)
    link.append(run)
    paragraph._p.append(link)


code = False
chapter_index = 0
for line in lines:
    if line.startswith("# "):
        chapter_index += 1
        paragraph = document.add_heading(line[2:], level=1)
        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), str(chapter_index))
        start.set(qn("w:name"), f"chapter_{chapter_index}")
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), str(chapter_index))
        paragraph.runs[0]._r.addprevious(start)
        paragraph._p.append(end)
    elif line.startswith("## "):
        document.add_heading(line[3:], level=2)
    elif line.startswith("[图:"):
        image_and_caption(line)
    elif line.startswith("[表:"):
        manual_table(TABLE_ROWS[line[3:-1]])
    elif line == "[代码开始]":
        code = True
    elif line == "[代码结束]":
        code = False
    elif line.startswith("https://"):
        linked_url(line)
    elif line and code:
        p = document.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(8.5)
    elif line:
        document.add_paragraph(line)

document.save(output)
assert len(chapters) == 14
print(output)
