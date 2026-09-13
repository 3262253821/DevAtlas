import MarkdownIt from "markdown-it";

// 只把模型返回的 Markdown 转成展示 HTML，不允许模型返回原始 HTML。
// 这样既能显示标题、列表、表格和代码块，也不会把回答当成可执行页面插入。
const renderer = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: false,
  typographer: false,
});

export function renderMarkdown(value: string): string {
  return renderer.render(value);
}
