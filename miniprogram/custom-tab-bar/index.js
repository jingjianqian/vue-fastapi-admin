// custom-tab-bar/index.js
Component({
  data: {
    selected: 0,
    color: "#7A7E83",
    selectedColor: "#18a058",
    list: [
      {
        pagePath: "/pages/home/home",
        text: "首页",
        iconPath: "assets/icons/home.png",
        selectedIconPath: "assets/icons/home-active.png"
      },
      {
        pagePath: "/pages/favorite/favorite",
        text: "收藏",
        iconPath: "assets/icons/favorite.png",
        selectedIconPath: "assets/icons/favorite-active.png"
      },
      {
        pagePath: "/pages/profile/profile",
        text: "我的",
        iconPath: "assets/icons/profile.png",
        selectedIconPath: "assets/icons/profile-active.png"
      }
    ]
  },

  attached() {
    // 获取当前页面路径
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const currentPath = '/' + currentPage.route
    
    // 设置选中的tab
    const index = this.data.list.findIndex(item => item.pagePath === currentPath)
    if (index > -1) {
      this.setData({
        selected: index
      })
    }
  },

  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset
      const url = data.path
      
      // 先更新选中状态
      this.setData({
        selected: data.index
      })
      
      // 跳转到对应页面
      wx.switchTab({
        url: url
      })
    }
  }
})