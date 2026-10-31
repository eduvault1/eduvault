/* Edu-Vault Unified Exam System SQL adapter.
 * The API stores exam-system records in the same SQL database used by app.py.
 */
(function(){
  'use strict';
  const base='/api/unified-exam';
  async function request(url, options={}){
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),8000);
    let response;
    try{
      response=await fetch(url,{credentials:'same-origin',...options,signal:options.signal||controller.signal});
    }catch(error){
      if(error.name==='AbortError') throw new Error('EduVault is taking too long to respond. Check the connection and try again.');
      throw error;
    }finally{clearTimeout(timeout)}
    const text=await response.text(); let data={};
    try{data=text?JSON.parse(text):{}}catch(_){data={message:text}}
    if(!response.ok) throw new Error(data.error||data.message||`Server request failed (${response.status})`);
    return data;
  }
  class Query{
    constructor(name,filters=[],limitN=null){this.name=name;this.filters=filters;this.limitN=limitN}
    where(field,op,value){return new Query(this.name,this.filters.concat([[field,op,value]]),this.limitN)}
    limit(n){return new Query(this.name,this.filters,n)}
    async get(){
      const data=await request(`${base}/records/${encodeURIComponent(this.name)}`);
      let docs=(data.records||[]).map(row=>({id:row.id,data:()=>row.data,ref:docRef(this.name,row.id)}));
      docs=docs.filter(doc=>this.filters.every(([f,op,v])=>{const a=doc.data()[f];if(op==='==')return String(a??'')===String(v??'');if(op==='!=')return String(a??'')!==String(v??'');return true}));
      if(this.limitN!=null)docs=docs.slice(0,this.limitN);
      return {docs,empty:docs.length===0,size:docs.length,forEach(fn){docs.forEach(fn)}};
    }
  }
  function docRef(collection,id){
    const path=`${base}/records/${encodeURIComponent(collection)}/${encodeURIComponent(id)}`;
    return {id:String(id),path:`${collection}/${id}`,
      set:(data,opt={})=>request(path,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:data||{},merge:!!opt.merge})}),
      delete:()=>request(path,{method:'DELETE'})};
  }
  function collection(name){return Object.assign(new Query(name),{doc:id=>docRef(name,id)})}
  const db={collection,batch(){const ops=[];return {delete(ref){ops.push(['delete',ref])},set(ref,data,opt){ops.push(['set',ref,data,opt])},async commit(){for(const [op,ref,data,opt] of ops){if(op==='delete')await ref.delete();else await ref.set(data,opt)}}}}};
  const storage={ref(){return storageRef('')}};
  function storageRef(path){return {child(part){return storageRef(path?`${path}/${part}`:part)},_url:null,async put(file){const fd=new FormData();fd.append('file',file);fd.append('path',path);const d=await request(`${base}/files`,{method:'POST',body:fd});this._url=d.url;return {ref:this}},async getDownloadURL(){if(!this._url)throw new Error('File has not been uploaded');return this._url}}}
  window.evDB=()=>db;
  window.evAuth=()=>({currentUser:{uid:'eduvault-session'}});
  window.evStorage=()=>storage;
  window.EvFieldValue={serverTimestamp:()=>new Date().toISOString()};
})();
