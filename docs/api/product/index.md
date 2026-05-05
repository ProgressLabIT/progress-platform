---
title: Product — API Reference
description: Product API operations — Progress Platform.
---

# Product API

Product catalogue, BOM management, product documentation, and product images.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /copy](/api/product/post-copy) — Copy a product to create a new variant.
- [GET /{product_key}](/api/product/get-product-key) — Fetch product data by key.
- [PATCH /{product_key}](/api/product/patch-product-key) — Update product fields.
- [PUT /{product_key}](/api/product/put-product-key) — Replace a product record.
- [DELETE /{product_key}](/api/product/delete-product-key) — Delete a product.
- [GET /{product_key}/stats](/api/product/get-product-key/stats) — Fetch production statistics for a product.
- [GET /{product_key}/bom](/api/product/get-product-key/bom) — Fetch the BOM for a product.
- [PUT /{product_key}/bom](/api/product/put-product-key/bom) — Replace the BOM for a product.
- [POST /{product_key}/doc](/api/product/post-product-key/doc) — Save a document to a product.
- [DELETE /{product_key}/doc/{doc_name}](/api/product/delete-product-key/doc/doc-name) — Delete a product document.
- [PUT /{product_key}/image](/api/product/put-product-key/image) — Replace the product image.
- [DELETE /{product_key}/image](/api/product/delete-product-key/image) — Delete the product image.
