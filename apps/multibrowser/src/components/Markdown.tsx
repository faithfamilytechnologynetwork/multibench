import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

// Authored prose is semi-trusted (repo content) but still rendered SAFELY:
// react-markdown does not render raw HTML by default (no rehype-raw), and rehype-sanitize
// strips anything dangerous. Styled with Tailwind Typography (`prose`).
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{children}</ReactMarkdown>
    </div>
  );
}
