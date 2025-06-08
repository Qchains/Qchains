# Here are your Instructions
build_nodejs_app:
  name: Build Node.js App
  runs-on: ubuntu-latest
  steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Setup Node.js environment
      uses: actions/setup-node@v4
      with:
        node-version: '20.x'
        cache: 'npm'
    
    - name: Validate dependencies lock file
      run: |
        if [ ! -f package-lock.json ] && [ ! -f yarn.lock ]; then
          echo "Error: Dependencies lock file is missing!"
          exit 1
        fi
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build application
      run: npm run build --if-present
    
    - name: Run tests
      run: npm test --if-present
