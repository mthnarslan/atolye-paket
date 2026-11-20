import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const {default:puppeteer}=await import(pathToFileURL(process.env.DOCUMENTARY_PUPPETEER).href);
const launch=puppeteer.launch.bind(puppeteer);
puppeteer.launch=async options=>{
  const browser=await launch({...options,args:[...(options.args||[]),'--force_high_performance_gpu']});
  const page=await browser.newPage();
  try{
    const info=await page.evaluate(()=>{const gl=document.createElement('canvas').getContext('webgl2',{powerPreference:'high-performance'});if(!gl)throw Error('WebGL2 unavailable');const ext=gl.getExtension('WEBGL_debug_renderer_info');return{vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)}});
    fs.appendFileSync(process.env.DOCUMENTARY_GPU_RECEIPT,JSON.stringify(info)+'\n');
    if(/swiftshader|llvmpipe|software/i.test(info.renderer))throw Error('Hardware WebGL required: '+info.renderer);
    return browser;
  }catch(error){await browser.close();throw error}finally{await page.close().catch(()=>{})}
};
