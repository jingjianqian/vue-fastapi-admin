// app.js
App({
  globalData: {
    userInfo: null,
    token: null,
    baseURL: 'http://localhost:9999/api/v1' // 后端接口地址，后续可改为正式环境
  },

  onLaunch(options) {
    console.log('小程序启动', options)
    
    // 检查是否有存储的 token
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      console.log('已登录，token:', token.substring(0, 20) + '...')
    } else {
      console.log('未登录，跳转登录页')
      // 可根据需要决定是否自动跳转登录
    }

    // 获取系统信息
    this.getSystemInfo()
  },

  onShow(options) {
    console.log('小程序显示', options)
  },

  onHide() {
    console.log('小程序隐藏')
  },

  // 获取系统信息
  getSystemInfo() {
    wx.getSystemInfo({
      success: (res) => {
        this.globalData.systemInfo = res
        console.log('系统信息:', res)
      }
    })
  },

  // 保存用户信息和token
  setUserInfo(userInfo, token) {
    this.globalData.userInfo = userInfo
    this.globalData.token = token
    wx.setStorageSync('userInfo', userInfo)
    wx.setStorageSync('token', token)
  },

  // 清除用户信息和token
  clearUserInfo() {
    this.globalData.userInfo = null
    this.globalData.token = null
    wx.removeStorageSync('userInfo')
    wx.removeStorageSync('token')
  },

  // 检查是否登录
  checkLogin() {
    return !!this.globalData.token
  }
})
