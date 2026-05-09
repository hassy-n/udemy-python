#!/usr/bin/env node
'use strict';

const DEFAULT_MODEL = 'gpt-4.1-mini';
const OPENAI_RESPONSES_URL = 'https://api.openai.com/v1/responses';

const THEMES = [
  'AI活用',
  '業務改善',
  'PM/PdM',
  '個人開発',
  '競合分析自動化',
];

const POST_TYPES = [
  '実体験風',
  '学び共有',
  '失敗談',
  'Tips',
  '問いかけ型',
];

function isDryRun() {
  return process.argv.includes('--dry-run') || process.env.DRY_RUN === 'true';
}

function todayJst() {
  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  }).format(new Date());
}

function buildPrompt() {
  return `以下の条件で、X（旧Twitter）投稿前の下書きを5本生成してください。直接投稿はせず、人間が確認・編集する前提です。\n\n目的:\n- Xに直接投稿しない\n- 毎日確認しやすい投稿案を作る\n- 将来X API投稿に拡張しやすいよう、構造化されたJSONで返す\n\nテーマ候補:\n${THEMES.map((theme) => `- ${theme}`).join('\n')}\n\n出力要件:\n- 投稿案を5本\n- 各投稿は日本語で140〜240文字程度\n- 1本目: 実体験風\n- 2本目: 学び共有\n- 3本目: 失敗談\n- 4本目: Tips\n- 5本目: 問いかけ型\n\nトーン:\n- 煽りすぎない\n- 情報商材っぽくしない\n- 誇大表現を避ける\n- 実務者が自然に投稿できる落ち着いた文体\n\n必ず次のJSONのみを返してください。Markdownや説明文は不要です。\n{\n  "posts": [\n    {\n      "type": "実体験風",\n      "theme": "AI活用",\n      "text": "投稿本文"\n    }\n  ]\n}`;
}

function buildInstructions() {
  return 'あなたは日本語のB2B/SaaS/プロダクト開発領域に強いSNS編集者です。投稿案は事実を断定しすぎず、読者に過度な期待を抱かせない自然な表現にしてください。';
}

function extractOutputText(responseJson) {
  if (typeof responseJson.output_text === 'string') {
    return responseJson.output_text;
  }

  const chunks = [];
  for (const item of responseJson.output ?? []) {
    for (const content of item.content ?? []) {
      if (content.type === 'output_text' && typeof content.text === 'string') {
        chunks.push(content.text);
      }
    }
  }

  return chunks.join('\n').trim();
}

function parsePosts(outputText) {
  const jsonStart = outputText.indexOf('{');
  const jsonEnd = outputText.lastIndexOf('}');

  if (jsonStart === -1 || jsonEnd === -1 || jsonEnd < jsonStart) {
    throw new Error('OpenAI response did not contain a JSON object.');
  }

  const parsed = JSON.parse(outputText.slice(jsonStart, jsonEnd + 1));

  if (!Array.isArray(parsed.posts) || parsed.posts.length !== 5) {
    throw new Error('Expected exactly 5 generated posts.');
  }

  return parsed.posts.map((post, index) => {
    const text = String(post.text ?? '').trim();
    if (!text) {
      throw new Error(`Post ${index + 1} is missing text.`);
    }

    return {
      type: String(post.type ?? POST_TYPES[index]),
      theme: String(post.theme ?? THEMES[index % THEMES.length]),
      text,
      chars: [...text].length,
    };
  });
}

async function generatePostsWithOpenAI() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY is required. Set it in GitHub Secrets or your local environment.');
  }

  const model = process.env.OPENAI_MODEL || DEFAULT_MODEL;
  const response = await fetch(OPENAI_RESPONSES_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      instructions: buildInstructions(),
      input: buildPrompt(),
      temperature: 0.7,
      max_output_tokens: 1200,
      store: false,
    }),
  });

  const responseText = await response.text();
  let responseJson;
  try {
    responseJson = JSON.parse(responseText);
  } catch (error) {
    throw new Error(`OpenAI API returned non-JSON response: ${responseText.slice(0, 500)}`);
  }

  if (!response.ok) {
    const message = responseJson.error?.message || response.statusText;
    throw new Error(`OpenAI API request failed (${response.status}): ${message}`);
  }

  const outputText = extractOutputText(responseJson);
  if (!outputText) {
    throw new Error('OpenAI response did not include output text.');
  }

  return parsePosts(outputText);
}

function generateDryRunPosts() {
  return [
    {
      type: '実体験風',
      theme: 'AI活用',
      text: '最近、会議メモの整理をAIに任せるようにしたら、議論の抜け漏れ確認に使う時間がかなり減りました。大事なのは丸投げではなく、最初に「決定事項・未決事項・次の行動」に分けてほしいと伝えること。最後は自分で見直す前提にすると、日々の小さな負担を減らしつつ、次のアクションも共有しやすくなります。',
    },
    {
      type: '学び共有',
      theme: '業務改善',
      text: '業務改善で学んだのは、最初から大きな自動化を狙わないことです。月1回の重い作業より、毎日10分発生する確認作業のほうが効果を感じやすいこともあります。頻度、手戻り、属人性の3点で見ると、改善テーマを選びやすくなります。まずは小さく試し、現場の反応を見て広げるのが安全です。数字と感想を一緒に残すと、次の改善にもつながります。',
    },
    {
      type: '失敗談',
      theme: 'PM/PdM',
      text: '以前、競合機能をまとめることに集中しすぎて、自社ユーザーが本当に困っている点の確認が後回しになったことがあります。比較表は便利ですが、意思決定の主役ではありません。競合分析は仮説作りの材料として扱うくらいがちょうどいいと感じています。最後はユーザー課題に戻る習慣が必要でした。見た目の差分だけで判断しないよう、今も気をつけています。',
    },
    {
      type: 'Tips',
      theme: '個人開発',
      text: '個人開発を続けるコツは、作る前に「最小の利用シーン」を1つだけ書くこと。誰が、いつ、何を楽にしたいのかを一文にすると、機能追加の判断がしやすくなります。完成度より、迷わず次の一手を決められる状態を作るのが大事です。READMEに残しておくと、数日空いても再開しやすくなります。未来の自分への引き継ぎメモにもなります。',
    },
    {
      type: '問いかけ型',
      theme: '競合分析自動化',
      text: '競合分析を自動化するとしたら、まず何を任せたいですか？ニュース収集、リリースノートの差分確認、価格ページの変更検知、SNSの反応整理。全部を一度にやるより、人が判断する前の「気づく」部分から始めるのが現実的かもしれません。チームで見るなら、通知の粒度も意外と大事です。多すぎる通知は見られなくなるので、最初に基準を決めたいところです。',
    },
  ].map((post) => ({ ...post, chars: [...post.text].length }));
}

function formatPosts(posts) {
  const lines = [];
  lines.push(`# X投稿案 (${todayJst()} JST)`);
  lines.push('');
  lines.push('> 注意: これは投稿前の下書きです。公開前に必ず人間が内容・事実関係・表現を確認してください。');
  lines.push('');

  posts.forEach((post, index) => {
    lines.push(`## ${index + 1}. ${post.type} / ${post.theme} (${post.chars}文字)`);
    lines.push(post.text);
    lines.push('');
  });

  return lines.join('\n');
}

async function writeGitHubStepSummary(markdown) {
  if (!process.env.GITHUB_STEP_SUMMARY) {
    return;
  }

  const fs = await import('node:fs/promises');
  await fs.appendFile(process.env.GITHUB_STEP_SUMMARY, `${markdown}\n`);
}

async function main() {
  const posts = isDryRun() ? generateDryRunPosts() : await generatePostsWithOpenAI();
  const markdown = formatPosts(posts);

  console.log(markdown);
  await writeGitHubStepSummary(markdown);
}

main().catch((error) => {
  console.error(`Failed to generate X post drafts: ${error.message}`);
  process.exit(1);
});
