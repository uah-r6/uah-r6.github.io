import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react'
import {createPortal} from 'react-dom'
import {Link} from 'react-router-dom'

export function StatHelp({label,help,section,embed=false}:{label:string;help:string;section:string;embed?:boolean}){
 const [open,setOpen]=useState(false),[position,setPosition]=useState({left:0,top:0,accent:'#82b8e8'})
 const button=useRef<HTMLButtonElement>(null),popup=useRef<HTMLSpanElement>(null),timer=useRef<ReturnType<typeof setTimeout>>(),id=useId()
 const cancel=()=>clearTimeout(timer.current)
 const closeLater=()=>{cancel();timer.current=setTimeout(()=>{if(document.activeElement!==button.current&&!popup.current?.contains(document.activeElement))setOpen(false)},160)}
 useEffect(()=>()=>clearTimeout(timer.current),[])
 useLayoutEffect(()=>{
  if(!open)return
  const place=()=>{const anchor=button.current;if(!anchor)return;const rect=anchor.getBoundingClientRect(),height=popup.current?.offsetHeight||170,width=Math.min(245,innerWidth-16)
   setPosition({left:Math.max(8,Math.min(rect.right-width,innerWidth-width-8)),top:rect.bottom+height+10>innerHeight?Math.max(8,rect.top-height-8):rect.bottom+8,accent:getComputedStyle(anchor).getPropertyValue('--accent')})}
  place();window.addEventListener('resize',place);window.addEventListener('scroll',place,true)
  return ()=>{window.removeEventListener('resize',place);window.removeEventListener('scroll',place,true)}
 },[open])
 useEffect(()=>{if(!open)return
  const outside=(e:PointerEvent)=>{const target=e.target as Node;if(!button.current?.contains(target)&&!popup.current?.contains(target))setOpen(false)}
  const escape=(e:KeyboardEvent)=>{if(e.key==='Escape'){button.current?.focus();setOpen(false)}}
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape)
  return ()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape)}
 },[open])
 const blur=(target:EventTarget|null)=>{if(target!==button.current&&!popup.current?.contains(target as Node))setOpen(false)}
 return <span className="stat-help" onMouseEnter={()=>{cancel();setOpen(true)}} onMouseLeave={closeLater}><button ref={button} className="help-button" type="button" aria-label={`About ${label}`} aria-haspopup="dialog" aria-expanded={open} aria-controls={open?id:undefined} onFocus={()=>setOpen(true)} onBlur={e=>blur(e.relatedTarget)} onClick={()=>setOpen(true)} onKeyDown={e=>{if(['Enter',' ','ArrowDown'].includes(e.key)){e.preventDefault();setOpen(true);requestAnimationFrame(()=>popup.current?.querySelector('a')?.focus())}}}>i</button>{open&&createPortal(<span ref={popup} id={id} role="dialog" aria-label={`${label} explained`} className="stat-popover floating-stat-help" style={{left:position.left,top:position.top,borderColor:position.accent}} onMouseEnter={cancel} onMouseLeave={closeLater} onBlur={e=>blur(e.relatedTarget)}><strong>{label}</strong><span>{help}</span><Link style={{color:position.accent}} to={`/methodology/${section}`} target={embed?'_blank':undefined} rel={embed?'noopener':undefined}>Learn more →</Link><button type="button" aria-label={`Close ${label} explanation`} onClick={()=>{button.current?.focus();setOpen(false)}}>×</button></span>,document.body)}</span>
}
