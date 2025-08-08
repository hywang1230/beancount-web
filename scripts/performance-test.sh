#!/bin/bash

# 性能测试脚本
echo "🚀 开始性能测试..."

# 构建优化后的代码
echo "📦 构建项目..."
npm run build

# 启动服务器
echo "🌐 启动预览服务器..."
npm run preview &
SERVER_PID=$!

# 等待服务器启动
sleep 5

# 使用 Lighthouse 进行性能测试
echo "🔍 运行 Lighthouse 性能测试..."
npx lighthouse http://localhost:5173/h5/transactions \
  --preset=mobile \
  --output=json \
  --output-path=./performance-report.json \
  --quiet

# 提取关键指标
echo "📊 分析性能指标..."
node -e "
const report = require('./performance-report.json');
const metrics = report.lhr.audits;

console.log('\\n🎯 性能指标:');
console.log('FCP (首次内容绘制):', metrics['first-contentful-paint'].displayValue);
console.log('LCP (最大内容绘制):', metrics['largest-contentful-paint'].displayValue);
console.log('CLS (累积布局偏移):', metrics['cumulative-layout-shift'].displayValue);
console.log('TBT (总阻塞时间):', metrics['total-blocking-time'].displayValue);
console.log('Speed Index:', metrics['speed-index'].displayValue);

const performance = report.lhr.categories.performance.score * 100;
console.log('\\n📈 性能评分:', performance.toFixed(1) + '/100');

if (performance >= 90) {
  console.log('✅ 性能优秀!');
} else if (performance >= 70) {
  console.log('⚠️ 性能良好，仍有优化空间');
} else {
  console.log('❌ 性能需要改进');
  process.exit(1);
}
"

# 清理
kill $SERVER_PID
echo "✨ 性能测试完成!"
