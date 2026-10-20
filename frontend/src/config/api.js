/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: 'http://127.0.0.1:8000',
}

export const aiChatConfig = {
  // OpenAI 兼容地址：阿里云百炼专属 MaaS 端点（需与下方 apiKey 配套使用）
  // 末尾必须带 /chat/completions，AIChat.vue 直接 fetch 该地址，不做路径拼接
  apiEndpoint: 'https://ws-mq4sk46skvavpo4v.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions',
  
  // API Key：从环境变量读取，禁止硬编码。
  // 在 frontend/.env.local 中配置 VITE_DASHSCOPE_API_KEY=xxx（该文件已被 git 忽略）
  // 注意：VITE_ 前缀变量会在构建时内联进产物，仅适用于本地开发；生产环境应改由后端代理转发
  apiKey: import.meta.env.VITE_DASHSCOPE_API_KEY || '',
  
  // 使用的模型
  model: 'qwen3.8-flash'
}
