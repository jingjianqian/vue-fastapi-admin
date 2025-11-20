// pages/profile/profile.js
const app = getApp()

Page({
  data: {
    userInfo: {}
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    this.loadUserInfo()
  },

  loadUserInfo() {
    const userInfo = wx.getStorageSync('userInfo')
    this.setData({ userInfo: userInfo || {} })
  },

  onMyFavorites() {
    wx.switchTab({
      url: '/pages/favorite/favorite'
    })
  },

  onAbout() {
    wx.showToast({
      title: '关于页面待开发',
      icon: 'none'
    })
  },

  onLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.clearUserInfo()
          wx.reLaunch({
            url: '/pages/login/login'
          })
        }
      }
    })
  }
})
