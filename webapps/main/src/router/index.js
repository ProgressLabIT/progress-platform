import Vue from "vue";
import VueRouter from "vue-router";
// import ProductList from "@/views/ProductList.vue";
// import ProductScreen from "@/components/ProductScreen.vue";
// import Login from "@/views/Login.vue";



Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    redirect: { name: 'login' }
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginScreen.vue")
  },
  {
    path: "/product",
    name: "productList",
    component: () => import("@/views/ProductList.vue"),
    // props: (route) => ({
    //   show_images: route.query.show_images,
    //   filter_inactive: route.query.filter_inactive
    // }),
    children: [
      {
        path: "new",
        name: "newProduct",
        component: () => import("@/views/ProductNew.vue")
      },
    ]
  },
  {
    path: "/product/:product_key",
    redirect: { name: "productHome" },
    component: () => import ("@/components/ProductScreen.vue"),
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
      },
    ]
  },
  {
    path: "/production",
    name: "productionOverview",
    redirect: { name: 'workOrderList' },
    component: () => import("@/views/ProductionOverview.vue"),
    children: [
      {
        path: "work-order",
        name: 'workOrderList',
        component: () => import ("@/components/WorkOrderList.vue"),
      },
      {
        path: "work-order/new",
        name: "newWorkOrder",
        component: () => import("@/views/WorkOrderNew.vue")
      },
      {
        path: "job/:department?",
        name: 'jobList',
        component: () => import ("@/components/JobList.vue"),
      }
    ]
  },
  {
    path: "/production/:wo_key",
    name: "workOrderScreen",
    redirect: { name: "workOrderHome"},
    component: () => import ("@/components/WorkOrderScreen.vue"),
    props: true,
    children: [
      {
        path: "home",
        name: "workOrderHome",
        component: () => import ("@/views/WorkOrderHome.vue")
      }
    ]
  },
  {
    path: "*",
    name: "notFound",
    component: () => import ("@/views/404_NotFound.vue")
  }
] 
 

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes
});

export default router;
