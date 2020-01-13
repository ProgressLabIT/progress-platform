import Vue from "vue";
import VueRouter from "vue-router";
import ProductList from "@/views/ProductList.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "productList",
    component: ProductList,
    children: [
      {
        path: "new-product",
        name: "newProduct",
        component: () => import("@/views/NewProduct.vue")
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
