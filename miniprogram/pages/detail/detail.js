// pages/detail/detail.js
const api = require('../../api/index')

Page({
  data: {
    appId: null,
    appInfo: {},
    useMock: true
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ appId: id })
      this.loadDetail(id)
    }
  },

  loadDetail(id) {
    if (this.data.useMock) {
      // Mock 数据
      this.setData({
        appInfo: {
          id: id,
          name: `小程序${id}`,
          icon: `https://via.placeholder.com/200/18a058/ffffff?text=App${id}`,
          desc: '这是一个详细的小程序介绍，包含各种功能说明和使用方法。',
          is_favorited: false,
          qrcode_url: 'https://via.placeholder.com/400/18a058/ffffff?text=QRCode'
        }
      })
      return
    }

    api.getAppDetail(id).then((data) => {
      this.setData({ appInfo: data })
    })
  },

  onLaunch() {
    wx.showToast({
      title: '打开小程序功能待实现',
      icon: 'none'
    })
  },

  onToggleFavorite() {
    const { appInfo } = this.data
    this.setData({
      'appInfo.is_favorited': !appInfo.is_favorited
    })
    wx.showToast({
      title: appInfo.is_favorited ? '已取消收藏' : '收藏成功',
      icon: 'success'
    })
  }
})
