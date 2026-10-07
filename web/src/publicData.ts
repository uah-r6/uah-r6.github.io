import {useEffect,useState} from 'react'
const base = import.meta.env.BASE_URL + 'data/'
export function useData<T>(path:string) {
  const [data,setData]=useState<T|null>(null), [error,setError]=useState('')
  useEffect(()=>{
    setData(null);setError('');if(!path)return
    const controller=new AbortController()
    fetch(base+path,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error(`Data unavailable (${r.status})`);return r.json()}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)})
    return ()=>controller.abort()
  },[path]);return {data,error}
}
