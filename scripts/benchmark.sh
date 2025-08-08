#!/bin/bash

# 性能基准测试脚本
echo "📊 开始性能基准测试..."

# 测试函数
run_test() {
  local test_name=$1
  local url=$2
  
  echo "🧪 测试: $test_name"
  
  # 运行多次测试取平均值
  local total_fcp=0
  local total_lcp=0
  local runs=3
  
  for i in $(seq 1 $runs); do
    echo "  运行 $i/$runs..."
    
    npx lighthouse "$url" \
      --preset=mobile \
      --output=json \
      --output-path="./test-$i.json" \
      --quiet
    
    local fcp=$(node -e "console.log(require('./test-$i.json').lhr.audits['first-contentful-paint'].numericValue)")
    local lcp=$(node -e "console.log(require('./test-$i.json').lhr.audits['largest-contentful-paint'].numericValue)")
    
    total_fcp=$(echo "$total_fcp + $fcp" | bc)
    total_lcp=$(echo "$total_lcp + $lcp" | bc)
    
    rm "./test-$i.json"
  done
  
  local avg_fcp=$(echo "scale=2; $total_fcp / $runs" | bc)
  local avg_lcp=$(echo "scale=2; $total_lcp / $runs" | bc)
  
  echo "  平均 FCP: ${avg_fcp}ms"
  echo "  平均 LCP: ${avg_lcp}ms"
  echo ""
}

# 启动服务器
npm run preview &
SERVER_PID=$!
sleep 5

# 测试不同页面
run_test "交易列表页面" "http://localhost:5173/h5/transactions"
run_test "添加交易页面" "http://localhost:5173/h5/add-transaction" 
run_test "首页" "http://localhost:5173/h5/dashboard"

# 清理
kill $SERVER_PID
echo "✅ 基准测试完成!"
