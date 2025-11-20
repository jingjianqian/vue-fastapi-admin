// pages/home/home.js
const api = require('../../api/index')

Page({
  data: {
    loading: false,
    searchKeyword: '',
    selectedCategory: null,
    banners: [],
    categories: [],
    topApps: [],
    appList: [],
    useMock: false // 使用真实接口
  },

  onLoad(options) {
    console.log('首页加载')
    this.loadHomeData()
  },

  onShow() {
    console.log('首页显示')
  },

  onPullDownRefresh() {
    this.loadHomeData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载首页数据
   */
  loadHomeData() {
    if (this.data.useMock) {
      return this.loadMockData()
    }

    this.setData({ loading: true })
    return api.getHome()
      .then((data) => {
        this.setData({
          banners: data.banners || [],
          categories: data.categories || [],
          topApps: data.top || [],
          appList: data.list || []
        })
      })
      .catch((err) => {
        console.error('加载首页数据失败', err)
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  /**
   * 加载 Mock 数据
   */
  loadMockData() {
    this.setData({ loading: true })
    
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockData = {
          banners: [
            { id: 1, image_url: 'https://via.placeholder.com/750x300/18a058/ffffff?text=Banner1' },
            { id: 2, image_url: 'https://via.placeholder.com/750x300/2ec973/ffffff?text=Banner2' }
          ],
          categories: [
            { id: 1, name: '全部', icon_url: '' },
            { id: 2, name: '工具', icon_url: '' },
            { id: 3, name: '生活', icon_url: '' },
            { id: 4, name: '娱乐', icon_url: '' },
            { id: 5, name: '教育', icon_url: '' }
          ],
          topApps: [
            { id: 1, name: '小程序1', icon: 'https://via.placeholder.com/120/18a058/ffffff?text=App1', desc: '这是一个小程序' },
            { id: 2, name: '小程序2', icon: 'https://via.placeholder.com/120/2ec973/ffffff?text=App2', desc: '这是一个小程序' },
            { id: 3, name: '小程序3', icon: 'https://via.placeholder.com/120/36ad6a/ffffff?text=App3', desc: '这是一个小程序' },
            { id: 4, name: '小程序4', icon: 'https://via.placeholder.com/120/4fb082/ffffff?text=App4', desc: '这是一个小程序' }
          ],
          appList: [
            { id: 1, name: '小程序A', icon: 'https://via.placeholder.com/80/18a058/ffffff?text=A', desc: '这是小程序A的描述' },
            { id: 2, name: '小程序B', icon: 'https://via.placeholder.com/80/2ec973/ffffff?text=B', desc: '这是小程序B的描述' },
            { id: 3, name: '小程序C', icon: 'https://via.placeholder.com/80/36ad6a/ffffff?text=C', desc: '这是小程序C的描述' },
            { id: 4, name: '小程序D', icon: 'https://via.placeholder.com/80/4fb082/ffffff?text=D', desc: '这是小程序D的描述' },
            { id: 5, name: '小程序E', icon: 'https://via.placeholder.com/80/63b898/ffffff?text=E', desc: '这是小程序E的描述' }
          ]
        }

        this.setData({
          banners: mockData.banners,
          categories: mockData.categories,
          topApps: mockData.topApps,
          appList: mockData.appList,
          loading: false
        })
        resolve()
      }, 500)
    })
  },

  /**
   * 搜索输入
   */
  onSearchInput(e) {
    this.setData({
      searchKeyword: e.detail.value
    })
  },

  /**
   * 分类点击
   */
  onCategoryTap(e) {
    const categoryId = e.currentTarget.dataset.id
    this.setData({
      selectedCategory: categoryId
    })
    console.log('选择分类', categoryId)
    // 根据分类筛选数据
  },

  /**
   * 小程序点击
   */
  onAppTap(e) {
    const appId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/detail/detail?id=${appId}`
    })
  }
})
