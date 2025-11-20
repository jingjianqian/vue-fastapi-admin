// pages/favorite/favorite.js
Page({
  data: {
    list: [],
    useMock: true
  },

  onLoad() {
    this.loadFavorites()
  },

  onShow() {
    this.loadFavorites()
  },

  loadFavorites() {
    if (this.data.useMock) {
      this.setData({
        list: [
          { id: 1, name: '收藏的小程序1', icon: 'https://via.placeholder.com/80/18a058/ffffff?text=F1', desc: '已收藏' },
          { id: 2, name: '收藏的小程序2', icon: 'https://via.placeholder.com/80/2ec973/ffffff?text=F2', desc: '已收藏' }
        ]
      })
    }
  },

  onAppTap(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/detail/detail?id=${id}`
    })
  }
})
