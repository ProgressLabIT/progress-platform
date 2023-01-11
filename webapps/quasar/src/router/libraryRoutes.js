const libraryRoutes = [
  {
    path: "library",
    name: "libraryRoot",
    meta: { scope: "library", screen_title: true },
    component: () => import("@/components/BaseEmptyParentRoute.vue"),
    redirect: { name: 'productList' },
    children: [
      {
        path: "product-list",
        name: "productList",
        component: () => import("@/views/ProductList.vue"),
        children: [
          {
            path: "new",
            name: "newProduct",
            component: () => import("@/views/ProductNew.vue")
          }
        ]
      },
      {
        path: "product/:product_key",
        redirect: { name: "productHome" },
        component: () => import("@/components/ProductScreen.vue"),
        props: true,
        children: [
          {
            path: "home",
            name: "productHome",
            component: () => import("@/views/ProductHome.vue")
          },
          {
            path: "process",
            name: "productionProcess",
            component: () => import("@/views/ProductionProcess.vue")
          },
          {
            path: "bom",
            name: "bom",
            component: () => import("@/views/ProductBom.vue")
          }
        ]
      }
    ]
  }
]

export default libraryRoutes
