import { defineConfig } from 'vitepress'
import {
  PageProperties,
  PagePropertiesMarkdownSection
} from '@nolebase/vitepress-plugin-page-properties/vite';
import {
  GitChangelog,
  GitChangelogMarkdownSection,
} from '@nolebase/vitepress-plugin-git-changelog/vite';
import { InlineLinkPreviewElementTransform } from '@nolebase/vitepress-plugin-inline-link-preview/markdown-it';
import timeline from 'vitepress-markdown-timeline';
import taskLists from "markdown-it-task-lists";
import { groupIconMdPlugin, groupIconVitePlugin } from 'vitepress-plugin-group-icons';
import { transformerTwoslash } from '@shikijs/vitepress-twoslash';

export const shared = defineConfig({
  title: 'OS-26Fall-FDU',
  base: '/OS-26Fall-FDU.github.io/',
  lastUpdated: true,
  // Lab0 and Lab1 are available. Keep later labs out of the published site.
  srcExclude: process.env.OS_DOCS_PREVIEW_ALL === '1' ? [] : ['lab/lab2.md', 'lab/lab3.md', 'lab/lab4.md', 'lab/lab5.md', 'lab/lab6.md', 'lab/lab-final.md'],
  cleanUrls: true,
  metaChunk: true,
  vite: {
    ssr: {
      noExternal: [
        '@nolebase/*',
      ],
    },
    plugins: [
      GitChangelog({
        maxGitLogCount: 2000,
        repoURL: () => 'https://github.com/JiaXtian/OS-26Fall-FDU.github.io',
      }),
      GitChangelogMarkdownSection({
        exclude: (id) => id.endsWith('index.md'),
        sections: {
          // 禁用页面历史
          disableChangelog: true,
          // 禁用贡献者
          disableContributors: true,
        },
      }) as any,
      PageProperties(),
      PagePropertiesMarkdownSection({
        excludes: [
          'index.md',
        ],
      }),
      groupIconVitePlugin({
        customIcon: {
          ts: 'logos:typescript',
          js: 'logos:javascript', //js图标
          md: 'logos:markdown', //markdown图标
          css: 'logos:css-3', //css图标
        },
      })
    ]
  },
  markdown: {
    math: true,
    config: (md) => {
      // 时间线
      md.use(timeline)
      // 任务列表
      md.use(taskLists)
      // 行内链接预览
      md.use(InlineLinkPreviewElementTransform)
      // 代码组图标
      md.use(groupIconMdPlugin)
    },
    attrs: { disable: true },
    codeTransformers: [
      transformerTwoslash()
    ]
  },

  sitemap: {
    hostname: 'https://jiaxtian.github.io/OS-26Fall-FDU.github.io/',
    transformItems(items) {
      return items.filter((item) => !item.url.includes('migration'))
    }
  },

  /* prettier-ignore */
  head: [
    [
      'link',
      {
        rel: 'icon',
        type: 'image/png',
        sizes: '32x32',
        href: '/OS-26Fall-FDU.github.io/assets/logo.png'
      }
    ],
    ['link', { rel: 'icon', type: 'image/png', sizes: '16x16', href: '/OS-26Fall-FDU.github.io/assets/logo.png' }],
    ['link', { rel: 'apple-touch-icon', sizes: '180x180', href: '/OS-26Fall-FDU.github.io/assets/logo.png' }],
    ['link', { rel: 'mask-icon', href: '/OS-26Fall-FDU.github.io/assets/logo.png', color: '#5bbad5' }],
    ['meta', { name: 'theme-color', content: '#5f67ee' }],
  ],

  themeConfig: {
    logo: { src: '/assets/logo.png', width: 24, height: 24 },
    //开启本地搜索
    search: {
      provider: 'local'
    },
    socialLinks: [{ icon: 'github', link: 'https://github.com/rfieldsy/OS-26Fall-FDU' }]
  }
})
