// Load environment variables from .env (if present)
import 'dotenv/config'
import { Bot } from "@maxhub/max-bot-api"

// Guard: require BOT_TOKEN to avoid confusing runtime errors when starting the bot
const token = process.env.BOT_TOKEN
if (!token) {
  console.error('Missing BOT_TOKEN environment variable. Set BOT_TOKEN and retry (e.g. export BOT_TOKEN=your_token)')
  process.exit(1)
}

const bot = new Bot(token)

// Установка подсказок с доступными командами
bot.api.setMyCommands([
  {
    name: 'ping',
    description: 'Сыграть в пинг-понг'
  },
]);

// Обработчик события запуска бота
bot.on('bot_started', (ctx) => ctx.reply('Привет! Отправь мне команду /ping, чтобы сыграть в пинг-понг'))

// Обработчик команды '/ping'
bot.command('ping', (ctx) => ctx.reply('pong'))

// Обработчик для сообщения с текстом 'hello'
bot.hears('hello', (ctx) => ctx.reply('world'))

// Обработчик для всех остальных входящих сообщения
bot.on('message_created', (ctx) => ctx.reply(ctx.message.body.text || ""))

bot.start()
