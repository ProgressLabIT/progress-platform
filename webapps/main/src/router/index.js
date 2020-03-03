import Vue from "vue";
import VueRouter from "vue-router";
import ProductList from "@/views/ProductList.vue";
import ModalScreen from "@/components/ModalScreen.vue";
import Login from "@/views/Login.vue";



Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    redirect: { name: 'login' }
  },
  {
    path: "/login",
    name: "login",
    component: Login
  },
  {
    path: "/product",
    name: "productList",
    component: ProductList,
    children: [
      {
        path: "new-product",
        name: "newProduct",
        component: () => import("@/views/NewProduct.vue")
      },
      {
        path: ":item_key",
        redirect: { name: "productHome" },
        component: ModalScreen,
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
            component: () => import("@/views/BillOfMaterials.vue")
          },
        ]
      }
    ] 
  },
  
  
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes
});

export default router;
